"""Scheme Navigator sub-agent — finds relevant government support schemes.

Uses the ``find_schemes`` skill (need -> scheme matching over a curated KB).
"""
from __future__ import annotations

from google.adk.agents import LlmAgent

from sprout.config import MODEL
from sprout.security.guardrails import apply_guardrails
from sprout.skills import find_schemes

scheme_navigator = apply_guardrails(
    LlmAgent(
        name="scheme_navigator",
        model=MODEL,
        description=(
            "Finds government agricultural schemes (income support, loans, crop "
            "insurance, irrigation subsidy, organic, market access) matching a "
            "farmer's need, with eligibility and how to apply."
        ),
        instruction=(
            "You are the Scheme Navigator. Call `find_schemes` with the farmer's "
            "need. Present the top 1-2 matches clearly: what the benefit is, who "
            "qualifies, and the steps to apply, plus the official website. "
            "Always warn the farmer to apply only through official channels and "
            "never to share OTPs or pay middlemen. Keep it simple and encouraging."
        ),
        tools=[find_schemes],
    )
)
