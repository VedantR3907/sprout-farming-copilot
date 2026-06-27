"""Skill: find_schemes.

Matches a farmer's described need (free text) against a curated knowledge base
of government agricultural support schemes and returns the most relevant ones.

Pure function — unit-testable, no network.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent.parent / "data" / "schemes.json"

# Map common farmer phrases to scheme tags for better recall.
_SYNONYMS = {
    "money": "income", "cash": "income", "support": "income", "fund": "income",
    "loan": "credit", "borrow": "credit", "interest": "credit",
    "insure": "insurance", "insurance": "insurance", "damage": "risk",
    "flood": "flood", "drought": "drought", "pest": "pest", "disease": "pest",
    "water": "irrigation", "drip": "irrigation", "sprinkler": "irrigation",
    "organic": "organic", "soil": "soil", "fertilizer": "fertilizer",
    "sell": "market", "price": "market", "mandi": "market", "trade": "market",
}


def _load() -> list[dict]:
    with open(_DATA, encoding="utf-8") as fh:
        return json.load(fh)["schemes"]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", (text or "").lower()))


def find_schemes(need: str, top_k: int = 3) -> dict[str, Any]:
    """Find government schemes relevant to a farmer's need.

    Args:
        need: Free text describing what the farmer wants help with
            (e.g. "I need a low-interest loan for seeds" or "insurance against drought").
        top_k: Maximum number of schemes to return.

    Returns:
        Ranked relevant schemes with how-to-apply info and official links.
    """
    schemes = _load()
    tokens = _tokens(need)
    if not tokens:
        return {"error": "Tell me what you need help with (money, loan, insurance, water, etc.)."}

    # Expand tokens with synonym tags.
    wanted_tags = set(tokens)
    for tok in tokens:
        if tok in _SYNONYMS:
            wanted_tags.add(_SYNONYMS[tok])

    scored = []
    for s in schemes:
        tagset = set(s["tags"])
        text_tokens = _tokens(s["name"] + " " + s["benefit"])
        overlap = (wanted_tags & tagset) | (tokens & text_tokens)
        if not overlap:
            continue
        scored.append((len(overlap), sorted(overlap), s))

    scored.sort(key=lambda t: t[0], reverse=True)
    if not scored:
        return {
            "need": need,
            "matches": [],
            "message": "No direct match. Common options: PM-KISAN (income), KCC (loans), "
            "PMFBY (insurance), PMKSY (irrigation). Ask about one of these.",
        }

    return {
        "need": need,
        "matches": [
            {
                "scheme": s["name"],
                "benefit": s["benefit"],
                "who_qualifies": s["who"],
                "how_to_apply": s["how"],
                "matched_on": overlap,
                "official_site": s["official"],
            }
            for _, overlap, s in scored[: int(top_k)]
        ],
        "disclaimer": "Scheme details change. Always verify eligibility and steps on the "
        "official portal before applying, and never share OTPs or pay 'agents'.",
    }
