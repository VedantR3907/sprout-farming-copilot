"""Skill: diagnose_crop.

Matches a free-text symptom description (plus optional crop) against a curated
crop-disease knowledge base and returns ranked likely causes with organic +
chemical remedies and prevention tips.

Pure function — no LLM or network required, so it is fully unit-testable and
free to run.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent.parent / "data" / "crop_diseases.json"


def _load() -> list[dict]:
    with open(_DATA, encoding="utf-8") as fh:
        return json.load(fh)["diseases"]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", (text or "").lower()))


def diagnose_crop(symptoms: str, crop: str = "") -> dict[str, Any]:
    """Diagnose a likely crop problem from described symptoms.

    Args:
        symptoms: Free text describing what the farmer sees
            (e.g. "yellow leaves with brown concentric ring spots").
        crop: Optional crop name to narrow results (e.g. "tomato").

    Returns:
        Ranked candidate problems with remedies, or guidance if no match.
    """
    diseases = _load()
    crop_key = (crop or "").strip().lower()
    sym_tokens = _tokens(symptoms)
    if not sym_tokens:
        return {"error": "Please describe the symptoms you see on the plant."}

    scored = []
    for d in diseases:
        if crop_key and d["crop"] not in (crop_key, "any"):
            continue
        # score = overlap of symptom phrase words with the candidate's symptom words
        cand_tokens: set[str] = set()
        for s in d["symptoms"]:
            cand_tokens |= _tokens(s)
        overlap = sym_tokens & cand_tokens
        if not overlap:
            continue
        # bonus for exact phrase matches
        phrase_bonus = sum(1 for s in d["symptoms"] if s.lower() in symptoms.lower())
        score = len(overlap) + 2 * phrase_bonus
        if crop_key and d["crop"] == crop_key:
            score += 1  # prefer crop-specific over generic "any"
        scored.append((score, sorted(overlap), d))

    scored.sort(key=lambda t: t[0], reverse=True)
    if not scored:
        return {
            "crop": crop_key or "unspecified",
            "diagnosis": [],
            "message": "No clear match. Note plant part affected, spot colour/shape, "
            "weather, and whether insects are visible, then ask again. "
            "Consider sharing a photo with a local extension officer.",
        }

    top = scored[:3]
    return {
        "crop": crop_key or "unspecified",
        "diagnosis": [
            {
                "problem": d["name"],
                "matched_signs": overlap,
                "confidence": _confidence(score, top[0][0]),
                "organic_remedy": d["organic"],
                "chemical_remedy": d["chemical"],
                "prevention": d["prevention"],
            }
            for score, overlap, d in top
        ],
        "disclaimer": "AI suggestion only. Confirm with a local agri-expert before "
        "applying chemicals, and always follow product label dosages.",
    }


def _confidence(score: int, best: int) -> str:
    ratio = score / best if best else 0
    if ratio >= 0.9:
        return "high"
    if ratio >= 0.5:
        return "medium"
    return "low"
