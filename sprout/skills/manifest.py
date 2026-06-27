"""Agent Skill manifests.

A *skill* in Sprout is a self-contained, declaratively-described capability:
metadata (what it does, example prompts, tags) plus a pure callable. This mirrors
the A2A/ADK ``AgentSkill`` concept so each capability is discoverable, testable,
and reusable across agents — not buried inside a prompt.

The registry below is the single source of truth; agents pull their tools and
the notebook/README render the skill catalogue from it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from sprout.skills.diagnose_crop import diagnose_crop
from sprout.skills.find_schemes import find_schemes
from sprout.skills.plan_irrigation import plan_irrigation


@dataclass(frozen=True)
class AgentSkill:
    """Declarative description of one reusable agent capability."""

    id: str
    name: str
    description: str
    tags: list[str]
    examples: list[str]
    fn: Callable = field(repr=False)


SKILLS: dict[str, AgentSkill] = {
    "diagnose_crop": AgentSkill(
        id="diagnose_crop",
        name="Crop Doctor",
        description=(
            "Diagnose likely crop diseases or pests from described symptoms and "
            "suggest organic + chemical remedies and prevention."
        ),
        tags=["diagnosis", "disease", "pest", "remedy"],
        examples=[
            "My tomato leaves have brown spots with concentric rings.",
            "White powdery coating on my plant leaves, what is it?",
            "Holes in cotton bolls and small caterpillars inside.",
        ],
        fn=diagnose_crop,
    ),
    "plan_irrigation": AgentSkill(
        id="plan_irrigation",
        name="Irrigation Planner",
        description=(
            "Recommend a water-wise irrigation amount and schedule from crop, soil, "
            "growth stage, and expected rainfall."
        ),
        tags=["irrigation", "water", "planning", "weather"],
        examples=[
            "How much should I water my rice on clay soil this week?",
            "It will rain 30mm — do I still irrigate my flowering tomatoes?",
        ],
        fn=plan_irrigation,
    ),
    "find_schemes": AgentSkill(
        id="find_schemes",
        name="Scheme Navigator",
        description=(
            "Find relevant government agricultural support schemes for a farmer's "
            "need (income, credit, insurance, irrigation, organic, market)."
        ),
        tags=["government", "subsidy", "finance", "insurance"],
        examples=[
            "I need a low-interest loan to buy seeds.",
            "Is there crop insurance against drought?",
            "Help with subsidy for drip irrigation.",
        ],
        fn=find_schemes,
    ),
}


def skill_catalogue() -> str:
    """Human-readable catalogue (used in README / notebook / agent cards)."""
    lines = []
    for s in SKILLS.values():
        lines.append(f"- **{s.name}** (`{s.id}`): {s.description}")
        lines.append(f"  - tags: {', '.join(s.tags)}")
        lines.append(f"  - e.g. \"{s.examples[0]}\"")
    return "\n".join(lines)
