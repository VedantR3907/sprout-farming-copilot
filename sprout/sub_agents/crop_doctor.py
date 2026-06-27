"""Crop Doctor sub-agent — diagnoses crop diseases / pests.

Uses the ``diagnose_crop`` skill (symptom matching over a curated disease KB).
"""
from __future__ import annotations

from google.adk.agents import LlmAgent

from sprout.config import MODEL
from sprout.security.guardrails import apply_guardrails
from sprout.skills import diagnose_crop

crop_doctor = apply_guardrails(
    LlmAgent(
        name="crop_doctor",
        model=MODEL,
        description=(
            "Diagnoses crop diseases and pests from a farmer's description of "
            "symptoms and recommends safe remedies. Use for 'what's wrong with my "
            "plant', spots/wilting/insects questions."
        ),
        instruction=(
            "You are the Crop Doctor. You can read both text and PHOTOS of plants.\n"
            "If the farmer sends a photo, examine it carefully: identify the crop, "
            "the affected part, and the visible symptoms (spot colour and shape, "
            "lesions, mould, wilting, or insects). Briefly tell the farmer what you "
            "see in the image.\n"
            "Then, whether from a photo or a description, call the `diagnose_crop` "
            "tool with a concise symptom description (and the crop if known). "
            "Explain the most likely problem in simple language, then give the "
            "organic remedy FIRST, the chemical remedy second, and one prevention "
            "tip. Always remind them to follow label dosages and consult a local "
            "expert before using chemicals. If a description is vague and there is "
            "no photo, ask one short clarifying question (plant part, spot colour/"
            "shape, insects visible)."
        ),
        tools=[diagnose_crop],
    )
)
