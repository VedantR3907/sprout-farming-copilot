"""Sprout root agent — the orchestrator of the multi-agent system.

The root agent greets the farmer, understands the request, and delegates to one
of three specialist sub-agents:

    root_agent (orchestrator)
      ├── crop_doctor       — diagnose disease / pests
      ├── field_advisor     — weather, market, soil, crop pick, irrigation (MCP)
      └── scheme_navigator  — government support schemes

Security guardrails (PII redaction, injection block, unsafe-advice filter, tool
validation) are attached to every agent, including this one.

ADK discovers ``root_agent`` from this module.
"""
from __future__ import annotations

from google.adk.agents import LlmAgent

from sprout.config import GLOBAL_SAFETY_NOTE, MODEL
from sprout.security.guardrails import apply_guardrails
from sprout.skills.farmer_profile import get_farmer_profile, save_farmer_profile
from sprout.sub_agents import crop_doctor, field_advisor, scheme_navigator

root_agent = apply_guardrails(
    LlmAgent(
        name="sprout",
        model=MODEL,
        description="Sprout, a friendly AI farming co-pilot for smallholder farmers.",
        instruction=(
            f"{GLOBAL_SAFETY_NOTE}\n\n"
            "You are the coordinator. Greet farmers warmly and figure out what they "
            "need, then transfer to the right specialist:\n"
            "- Plant looks sick, spots, pests, wilting -> transfer to `crop_doctor`.\n"
            "- Weather, market/selling prices, soil, what crop to grow, irrigation "
            "/ watering -> transfer to `field_advisor`.\n"
            "- Money, loans, insurance, subsidies, government help -> transfer to "
            "`scheme_navigator`.\n"
            "For greetings or general questions, answer briefly yourself and ask a "
            "clarifying question. After a specialist answers, you may offer one "
            "relevant follow-up. Keep everything simple, kind, and practical.\n"
            "When the farmer shares their name, location/district, soil type, or "
            "crops, call `save_farmer_profile` to remember it. Call "
            "`get_farmer_profile` to reuse what you already know instead of "
            "asking again."
        ),
        tools=[save_farmer_profile, get_farmer_profile],
        sub_agents=[crop_doctor, field_advisor, scheme_navigator],
    )
)
