"""Farmer profile memory (ADK session state).

Lets Sprout remember a farmer's details across turns so they don't have to
repeat their location, soil, or crops every time. This demonstrates ADK
**session state** management: the tools read/write ``tool_context.state``,
which ADK persists for the session.

These tools are attached directly to the agents (not exported via
``skills/__init__`` or the skill manifest) so the offline skill tests stay free
of any ADK dependency.
"""
from __future__ import annotations

from typing import Optional

from google.adk.tools.tool_context import ToolContext

_PROFILE_KEY = "farmer_profile"


def save_farmer_profile(
    tool_context: ToolContext,
    name: Optional[str] = None,
    location: Optional[str] = None,
    soil_type: Optional[str] = None,
    crops: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict:
    """Remember the farmer's details for this conversation.

    Call this whenever the farmer shares who they are or about their farm
    (name, district/location, soil type, crops grown, or coordinates). Only the
    fields you pass are updated; existing details are kept.
    """
    profile = dict(tool_context.state.get(_PROFILE_KEY, {}))
    for key, value in {
        "name": name,
        "location": location,
        "soil_type": soil_type,
        "crops": crops,
        "latitude": latitude,
        "longitude": longitude,
    }.items():
        if value is not None and value != "":
            profile[key] = value
    tool_context.state[_PROFILE_KEY] = profile
    return {"saved": True, "profile": profile}


def get_farmer_profile(tool_context: ToolContext) -> dict:
    """Recall what we already know about the farmer (location, soil, crops, etc.)."""
    profile = tool_context.state.get(_PROFILE_KEY, {})
    if not profile:
        return {"profile": {}, "note": "No profile saved yet — ask the farmer if useful."}
    return {"profile": profile}
