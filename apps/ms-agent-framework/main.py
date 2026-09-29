"""FastAPI server: serves the demo UI and runs the briefing agent."""

import os
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from briefing_agent import build_agent

load_dotenv()  # must run before build_agent(), which reads OPENAI_* to pick the client

app = FastAPI(title="Microsoft Agent Framework demo")
AGENT, MODE = build_agent()


class BriefingRequest(BaseModel):
    city: str


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": MODE}


@app.post("/api/briefing")
async def briefing(req: BriefingRequest) -> dict[str, Any]:
    city = req.city.strip()
    if not city:
        raise HTTPException(status_code=400, detail="city is required")
    try:
        response = await AGENT.run(city)
    except Exception as exc:  # surface tool/LLM failures to the UI
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    call_names: dict[str, str] = {}
    steps: list[dict[str, Any]] = [{"kind": "user", "text": city}]
    for message in response.messages:
        for content in message.contents or []:
            if content.type == "function_call":
                call_names[content.call_id] = content.name
                steps.append(
                    {
                        "kind": "tool_call",
                        "name": content.name,
                        "arguments": content.arguments,
                        "call_id": content.call_id,
                    }
                )
            elif content.type == "function_result":
                steps.append(
                    {
                        "kind": "tool_result",
                        "name": call_names.get(content.call_id, "?"),
                        "result": str(content.result),
                        "call_id": content.call_id,
                    }
                )
    steps.append({"kind": "final", "text": response.text})
    return {"mode": MODE, "final": response.text, "steps": steps}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8787")))
