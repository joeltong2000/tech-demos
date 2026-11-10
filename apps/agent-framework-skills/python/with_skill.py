"""WITH-SKILL — written after reading vendor/skills/agent-framework-builder-python.

Path chosen: plain agent (references/agent-builder.md). Not harness / workflow.

Skill-guided choices applied here:
- Narrow distribution: agent-framework-core (skill Defaults — do not default to the meta-package)
- Agent(client=..., instructions=..., tools=[...]) wrapping a chat client
- @tool(approval_mode="never_require") on focused module-level functions (official sample style)
- Custom offline client subclasses BaseChatClient and composes FunctionInvocationLayer in the
  documented order (extensibility.md / custom_chat_client.py sample)
- load_dotenv() only when AF_CHAT_MODE requests a live provider; framework does not auto-load .env
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Mapping, Sequence
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


_DATA: dict[str, Any] = {}
_STATUS_CODES: dict[str, str] = {}


def load_store(path: Path) -> None:
    global _DATA, _STATUS_CODES
    _DATA = json.loads(path.read_text())
    _STATUS_CODES = dict(_DATA["statusCodes"])


# Skill: focused, typed, non-interactive tools; approval_mode never_require for read-only lookups.
@tool(approval_mode="never_require")
def get_job_status(job_number: int) -> str:
    """Look up a JD Edwards submitted batch job by job number."""
    for job in _DATA["jobs"]:
        if job["jobNumber"] == job_number:
            code = job["status"]
            return json.dumps(
                {
                    "jobNumber": job_number,
                    "reportId": job["reportId"],
                    "version": job["version"],
                    "description": job["description"],
                    "status": code,
                    "statusLabel": _STATUS_CODES.get(code, code),
                    "user": job["user"],
                    "queue": job["queue"],
                    "errorText": job.get("errorText"),
                }
            )
    return json.dumps({"error": f"Job {job_number} not found"})


@tool(approval_mode="never_require")
def list_active_jobs() -> str:
    """List JD Edwards submitted jobs that are not yet Done."""
    active = []
    for job in _DATA["jobs"]:
        code = job["status"]
        if code == "D":
            continue
        active.append(
            {
                "jobNumber": job["jobNumber"],
                "reportId": job["reportId"],
                "status": code,
                "statusLabel": _STATUS_CODES.get(code, code),
                "description": job["description"],
            }
        )
    return json.dumps(active)


class ScriptedOpsChatClient(FunctionInvocationLayer, BaseChatClient):
    """Offline scripted client.

    Layer order follows extensibility.md: FunctionInvocationLayer then BaseChatClient so the
    standard tool loop runs around _inner_get_response.
    """

    def __init__(self) -> None:
        super().__init__()
        self._turn = 0

    async def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> ChatResponse:
        if stream:
            raise NotImplementedError("Streaming is not used in this offline demo")

        self._turn += 1
        has_function_result = any(
            getattr(c, "type", None) == "function_result" for m in messages for c in (m.contents or [])
        )

        if has_function_result or self._turn > 1:
            return ChatResponse(
                messages=[
                    Message(
                        role="assistant",
                        contents=[
                            Content.from_text(
                                "Job 570213 (R31410 / Work Order Processing) is in Error (E). "
                                "errorText: Work order 451882 failed: branch/plant M30 record "
                                "invalid (error 0002E)."
                            )
                        ],
                    )
                ],
                model="scripted-ops-with-skill",
            )

        return ChatResponse(
            messages=[
                Message(
                    role="assistant",
                    contents=[
                        Content.from_function_call(
                            call_id="call_skill_1",
                            name="get_job_status",
                            arguments={"job_number": 570213},
                        )
                    ],
                )
            ],
            model="scripted-ops-with-skill",
        )


def create_chat_client() -> Any:
    """Skill: configuration is application-owned; pass provider settings explicitly."""
    mode = os.environ.get("AF_CHAT_MODE", "scripted").lower()
    if mode == "openai":
        # Skill: call load_dotenv() explicitly — framework will not do it for you.
        from dotenv import load_dotenv

        load_dotenv()
        raise RuntimeError(
            "Live OpenAI mode is documented in .env.example. Install agent-framework-openai and "
            "construct OpenAIChatClient / OpenAIChatCompletionClient per the skill provider table. "
            "This demo's default path stays scripted so CI needs no keys."
        )
    return ScriptedOpsChatClient()


def _print_response(response: Any) -> None:
    for message in response.messages:
        print(f"[{message.role}]")
        for content in message.contents or []:
            ctype = getattr(content, "type", None)
            if ctype == "function_call":
                print(f"  tool_call {content.name}({content.arguments})")
            elif ctype == "function_result":
                print(f"  tool_result {content.call_id}: {content.result}")
            elif getattr(content, "text", None):
                print(f"  {content.text}")
            else:
                print(f"  {content}")


async def main() -> None:
    data_path = find_data_file()
    load_store(data_path)
    client = create_chat_client()

    agent = Agent(
        client=client,
        instructions=(
            "You are a JD Edwards ops helper. Use the provided tools to look up batch job "
            "status from the Work with Submitted Jobs (WSJ) mock data. Answer briefly."
        ),
        name="jde-ops-helper",
        description="Offline JDE batch-job status helper (skill-guided).",
        tools=[get_job_status, list_active_jobs],
    )

    prompt = (
        "What is the status of job 570213? Include the report id and any error text."
    )
    print("=== Python with-skill (agent-framework-builder-python) ===")
    print(f"Data: {data_path}")
    print(f"Chat client: {type(client).__name__}")
    print()
    print(f"User: {prompt}")
    print()

    # Skill: create a session for a logical conversation.
    session = agent.create_session()
    response = await agent.run(prompt, session=session)
    _print_response(response)
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
    except Exception as exc:  # noqa: BLE001
        print(f"WITH-SKILL ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
