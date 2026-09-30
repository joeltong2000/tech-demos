"""Trip Briefing agent built on Microsoft Agent Framework.

The agent answers "give me a trip briefing for <city>" by calling two tools
(current weather and local time, both backed by the free Open-Meteo APIs) and
then composing a short briefing. The agent loop — tool schema advertising,
function invocation, message threading — is entirely Microsoft Agent Framework.

Two interchangeable chat clients drive the loop:

- OpenAIChatClient      when OPENAI_API_KEY is set (real LLM planning).
- ScriptedPlannerClient otherwise: a deterministic BaseChatClient that plans
  the same tool calls and composes the briefing from the tool results, so the
  demo runs end-to-end with no secrets.
"""

import json
import os
from collections.abc import Mapping, Sequence
from typing import Any

import httpx
from agent_framework import (
    Agent,
    BaseChatClient,
    ChatResponse,
    Content,
    FunctionInvocationLayer,
    Message,
    tool,
)
from agent_framework.openai import OpenAIChatClient

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Subset of WMO weather interpretation codes returned by Open-Meteo.
WMO_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
}


async def _geocode(client: httpx.AsyncClient, city: str) -> dict[str, Any]:
    resp = await client.get(GEOCODING_URL, params={"name": city, "count": 1})
    resp.raise_for_status()
    results = resp.json().get("results") or []
    if not results:
        raise ValueError(f"Unknown city: {city!r}")
    return results[0]


@tool
async def get_weather(city: str) -> str:
    """Get the current weather (temperature, conditions, wind) for a city."""
    async with httpx.AsyncClient(timeout=15) as client:
        place = await _geocode(client, city)
        resp = await client.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        resp.raise_for_status()
        current = resp.json()["current"]
    return json.dumps(
        {
            "city": place["name"],
            "country": place.get("country"),
            "temperature_c": current["temperature_2m"],
            "conditions": WMO_CODES.get(current["weather_code"], "unknown"),
            "wind_kmh": current["wind_speed_10m"],
        }
    )


@tool
async def get_local_time(city: str) -> str:
    """Get the current local time and timezone for a city."""
    async with httpx.AsyncClient(timeout=15) as client:
        place = await _geocode(client, city)
        resp = await client.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m",
                "timezone": "auto",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return json.dumps(
        {
            "city": place["name"],
            "timezone": data["timezone"],
            "utc_offset": data["timezone_abbreviation"],
            "local_time": data["current"]["time"],
        }
    )


class ScriptedPlannerClient(FunctionInvocationLayer, BaseChatClient):
    """Deterministic stand-in for the LLM.

    Implements the framework's chat-client protocol: on the first pass it
    "plans" calls to both tools; once the framework has executed them and fed
    the results back, it composes the final briefing. Everything between the
    two passes (tool dispatch, result threading) is real framework machinery.
    """

    async def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> ChatResponse:
        tool_results = [
            content
            for message in messages
            for content in (message.contents or [])
            if content.type == "function_result"
        ]
        if not tool_results:
            city = self._last_user_text(messages)
            return ChatResponse(
                messages=Message(
                    role="assistant",
                    contents=[
                        Content.from_function_call("call_weather", "get_weather", arguments={"city": city}),
                        Content.from_function_call("call_time", "get_local_time", arguments={"city": city}),
                    ],
                ),
                finish_reason="tool_calls",
            )
        return ChatResponse(
            messages=Message(role="assistant", contents=[Content.from_text(self._compose(tool_results))]),
            finish_reason="stop",
        )

    @staticmethod
    def _last_user_text(messages: Sequence[Message]) -> str:
        text = ""
        for message in messages:
            if str(message.role) == "user" and message.text:
                text = message.text
        return text.strip() or "Paris"

    @staticmethod
    def _compose(tool_results: list[Content]) -> str:
        weather: dict[str, Any] = {}
        local: dict[str, Any] = {}
        errors: list[str] = []
        for content in tool_results:
            if content.exception:
                errors.append(str(content.exception))
                continue
            try:
                data = json.loads(str(content.result))
            except (TypeError, ValueError):
                continue
            if "temperature_c" in data:
                weather = data
            elif "local_time" in data:
                local = data
        if not weather or not local:
            detail = f" ({errors[0]})" if errors else ""
            return f"I could not gather enough data for a briefing{detail}. Try another city."
        clock = local["local_time"].split("T")[-1]
        return (
            f"Trip briefing for {weather['city']}, {weather.get('country', '')}: "
            f"it is currently {clock} local time ({local['timezone']}). "
            f"The weather is {weather['conditions']} at {weather['temperature_c']}°C "
            f"with wind around {weather['wind_kmh']} km/h. "
            f"Pack accordingly and enjoy the trip!"
        )


def build_agent() -> tuple[Agent, str]:
    """Create the briefing agent. Returns (agent, mode_description)."""
    if os.environ.get("OPENAI_API_KEY"):
        model = os.environ.get("OPENAI_CHAT_MODEL_ID", "gpt-4o-mini")
        client: Any = OpenAIChatClient(model=model, base_url=os.environ.get("OPENAI_BASE_URL") or None)
        mode = f"openai:{model}"
    else:
        client = ScriptedPlannerClient()
        mode = "offline scripted planner"
    agent = Agent(
        client=client,
        name="TripBriefer",
        instructions=(
            "You are a trip briefing assistant. When the user names a city, call "
            "get_weather and get_local_time for that city, then reply with one short, "
            "friendly paragraph combining local time, weather, and a packing tip."
        ),
        tools=[get_weather, get_local_time],
    )
    return agent, mode
