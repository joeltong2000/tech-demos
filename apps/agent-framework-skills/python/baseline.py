"""BASELINE — written from generic / pre-skill knowledge of Microsoft Agent Framework.

Wrong first guesses (recorded in COMPARISON.md) before package introspection:
- Import ChatAgent / @ai_function (those names are stale; current surface is Agent / @tool)
- Assumed Microsoft.Extensions.AI-style OpenAI wiring; for offline we subclass BaseChatClient
  and mix in FunctionInvocationLayer so tools still run.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from agent_framework import (
    Agent,
    BaseChatClient,
    ChatResponse,
    Content,
    FunctionInvocationLayer,
    Message,
    tool,
)


def find_data_file() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in [
        here.parent / "data" / "jde-jobs.json",
        here / "data" / "jde-jobs.json",
        Path.cwd() / "data" / "jde-jobs.json",
        Path.cwd().parent / "data" / "jde-jobs.json",
    ]:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Could not locate data/jde-jobs.json")


class JdeJobStore:
    def __init__(self, path: Path) -> None:
        self._data = json.loads(path.read_text())
        self._status_codes = self._data["statusCodes"]

    @tool(description="Look up a JD Edwards submitted batch job by job number.")
    def get_job_status(self, job_number: int) -> str:
        """Look up a JD Edwards submitted batch job by job number."""
        for job in self._data["jobs"]:
            if job["jobNumber"] == job_number:
                code = job["status"]
                return json.dumps(
                    {
                        "jobNumber": job_number,
                        "reportId": job["reportId"],
                        "version": job["version"],
                        "description": job["description"],
                        "status": code,
                        "statusLabel": self._status_codes.get(code, code),
                        "user": job["user"],
                        "queue": job["queue"],
                        "errorText": job.get("errorText"),
                    }
                )
        return json.dumps({"error": f"Job {job_number} not found"})

    @tool(description="List JD Edwards submitted jobs that are not yet Done.")
    def list_active_jobs(self) -> str:
        """List JD Edwards submitted jobs that are not yet Done."""
        active = []
        for job in self._data["jobs"]:
            code = job["status"]
            if code == "D":
                continue
            active.append(
                {
                    "jobNumber": job["jobNumber"],
                    "reportId": job["reportId"],
                    "status": code,
                    "statusLabel": self._status_codes.get(code, code),
                    "description": job["description"],
                }
            )
        return json.dumps(active)


class ScriptedOpsChatClient(FunctionInvocationLayer, BaseChatClient):
    """Offline scripted client: first turn = get_job_status tool call; second = final answer."""

    def __init__(self) -> None:
        super().__init__()
        self._turn = 0

    async def _inner_get_response(
        self,
        *,
        messages: Any,
        stream: bool,
        options: Any,
        **kwargs: Any,
    ) -> ChatResponse:
        if stream:
            raise NotImplementedError("Streaming is not used in this offline demo")

        self._turn += 1
        has_function_result = any(
            getattr(c, "type", None) == "function_result"
            or c.__class__.__name__ == "FunctionResultContent"
            or (isinstance(c, Content) and getattr(c, "type", None) == "function_result")
            for m in messages
            for c in (m.contents or [])
        )

        if has_function_result or self._turn > 1:
            return ChatResponse(
                messages=Message(
                    "assistant",
                    [
                        Content.from_text(
                            "Job 570213 (R31410 / Work Order Processing) is in Error (E). "
                            "errorText: Work order 451882 failed: branch/plant M30 record "
                            "invalid (error 0002E)."
                        )
                    ],
                )
            )

        return ChatResponse(
            messages=Message(
                "assistant",
                [
                    Content.from_function_call(
                        call_id="call_baseline_1",
                        name="get_job_status",
                        arguments={"job_number": 570213},
                    )
                ],
            )
        )


async def main() -> None:
    data_path = find_data_file()
    store = JdeJobStore(data_path)
    client = ScriptedOpsChatClient()

    agent = Agent(
        client,
        instructions=(
            "You are a JD Edwards ops helper. Use the provided tools to look up batch job "
            "status from the Work with Submitted Jobs (WSJ) mock data. Answer briefly."
        ),
        name="jde-ops-helper-baseline",
        description="Offline JDE batch-job status helper (baseline, pre-skill).",
        tools=[store.get_job_status, store.list_active_jobs],
    )

    prompt = (
        "What is the status of job 570213? Include the report id and any error text."
    )
    print("=== Python baseline (without skill) ===")
    print(f"Data: {data_path}")
    print()
    print(f"User: {prompt}")
    print()

    response = await agent.run(prompt)
    for message in response.messages:
        print(f"[{message.role}]")
        for content in message.contents or []:
            ctype = getattr(content, "type", content.__class__.__name__)
            if ctype == "function_call" or hasattr(content, "name") and getattr(content, "arguments", None) is not None and getattr(content, "call_id", None):
                print(f"  tool_call {getattr(content, 'name', '?')}({getattr(content, 'arguments', {})})")
            elif ctype == "function_result" or getattr(content, "result", None) is not None and getattr(content, "call_id", None):
                print(f"  tool_result {getattr(content, 'call_id', '?')}: {getattr(content, 'result', content)}")
            elif getattr(content, "text", None):
                print(f"  {content.text}")
            else:
                print(f"  {content}")
    print()
    text = getattr(response, "text", None) or "".join(
        getattr(c, "text", "") or ""
        for m in response.messages
        for c in (m.contents or [])
    )
    print(f"Final: {text}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001 — surface for COMPARISON.md
        print(f"BASELINE ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
