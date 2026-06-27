"""Field Advisor sub-agent — weather, market prices, soil & crop selection.

This agent demonstrates the MCP integration: its data tools come from the custom
Sprout MCP server (``sprout/mcp_server/server.py``) connected over stdio via
ADK's ``McpToolset``. It also uses the local ``plan_irrigation`` skill.
"""
from __future__ import annotations

import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from sprout.config import MODEL, PROJECT_ROOT
from sprout.security.guardrails import apply_guardrails
from sprout.skills import plan_irrigation

# Launch the custom MCP server as a subprocess and speak MCP over stdio.
_field_tools_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "sprout.mcp_server.server"],
            cwd=str(PROJECT_ROOT),
        ),
    )
)

field_advisor = apply_guardrails(
    LlmAgent(
        name="field_advisor",
        model=MODEL,
        description=(
            "Provides weather forecasts, mandi market prices, soil guidance, "
            "data-driven crop recommendations, and irrigation plans. Use for "
            "weather, selling prices, what-to-grow, and watering questions."
        ),
        instruction=(
            "You are the Field Advisor. Use your MCP tools for live/real data:\n"
            "- `get_weather_forecast(latitude, longitude)` for weather (ask for the "
            "farmer's location/district if you don't have coordinates).\n"
            "- `get_market_prices(crop)` for selling prices and sell/hold hints.\n"
            "- `get_soil_recommendation(crop, soil_type)` for soil suitability.\n"
            "- `recommend_crop(...)` (backed by a real dataset) when the farmer asks "
            "what to grow and can give soil nutrients/pH and climate.\n"
            "Use the `plan_irrigation` skill for watering schedules; if you have a "
            "weather forecast, pass its expected rainfall into the plan. "
            "Keep answers short, practical, and in plain language."
        ),
        tools=[_field_tools_mcp, plan_irrigation],
    )
)
