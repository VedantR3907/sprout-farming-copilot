"""Security policies (pure logic).

These functions contain ALL the security decision-making and have **no ADK
dependency**, so they are fast, deterministic, and unit-testable offline.
``guardrails.py`` adapts them into ADK callbacks.

Three protections:
  1. PII redaction        -> redact_pii()
  2. Prompt-injection /    -> scan_input()
     jailbreak detection
  3. Unsafe-advice filter  -> scan_output()
  + tool argument validation -> validate_tool_args()
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# 1. PII redaction
# --------------------------------------------------------------------------- #
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Aadhaar-like: 12 digits, optionally grouped in 4s.
_AADHAAR_RE = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
# Credit/debit card-like: 13-16 digit runs (grouped or not).
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")
# Indian mobile: optional +91/0 then 10 digits starting 6-9.
_PHONE_RE = re.compile(r"\b(?:\+?91[ -]?|0)?[6-9]\d{9}\b")


@dataclass
class RedactionResult:
    text: str
    redactions: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.redactions)


def redact_pii(text: str) -> RedactionResult:
    """Replace emails, Aadhaar/card numbers, and phone numbers with placeholders.

    Order matters: longer numeric IDs are redacted before phone numbers so a
    12-digit Aadhaar is not partially eaten by the phone matcher.
    """
    if not text:
        return RedactionResult(text="")
    found: list[str] = []
    out = text

    def _sub(pattern: re.Pattern, label: str, s: str) -> str:
        def repl(_m):
            found.append(label)
            return f"[REDACTED_{label}]"
        return pattern.sub(repl, s)

    out = _sub(_EMAIL_RE, "EMAIL", out)
    out = _sub(_AADHAAR_RE, "ID", out)
    out = _sub(_CARD_RE, "CARD", out)
    out = _sub(_PHONE_RE, "PHONE", out)
    return RedactionResult(text=out, redactions=found)


# --------------------------------------------------------------------------- #
# 2. Prompt-injection / jailbreak detection
# --------------------------------------------------------------------------- #
_INJECTION_PATTERNS = [
    r"ignore (all |the )?(previous|prior|above) (instructions|prompts)",
    r"disregard (your|the|all) (instructions|rules|guidelines)",
    r"forget (your|the|all|everything) (instructions|rules|above)",
    r"reveal (your|the) (system )?(prompt|instructions)",
    r"(print|show|repeat) (your|the) (system )?(prompt|instructions)",
    r"you are now (a|an|in)",
    r"developer mode",
    r"jailbreak",
    r"\bdan\b mode",
    r"act as (an? )?(unfiltered|uncensored)",
    r"bypass (your|the|all) (safety|filters|guardrails)",
]
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


@dataclass
class ScanResult:
    blocked: bool
    reasons: list[str] = field(default_factory=list)


def scan_input(text: str) -> ScanResult:
    """Flag prompt-injection / jailbreak attempts in user input."""
    reasons = [p.pattern for p in _INJECTION_RE if p.search(text or "")]
    return ScanResult(blocked=bool(reasons), reasons=reasons)


# --------------------------------------------------------------------------- #
# 3. Unsafe-advice output filter
# --------------------------------------------------------------------------- #
# Restricted/banned or dangerously-misused substances and self-harm cues.
_UNSAFE_PATTERNS = [
    r"\bddt\b",
    r"endosulfan",
    r"monocrotophos",
    r"\bparaquat\b",
    r"drink (the )?(pesticide|insecticide|chemical)",
    r"(spray|apply) .* (on|near) (children|people|food) directly",
    r"double|triple the (label )?(dose|dosage)",
    r"mix .* (bleach|acid) .* (pesticide|chemical)",
    r"(harm|kill|hurt) (yourself|myself|someone)",
]
_UNSAFE_RE = [re.compile(p, re.IGNORECASE) for p in _UNSAFE_PATTERNS]

_SAFETY_FOOTER = (
    "\n\n⚠️ Safety note: follow product labels and local regulations, keep "
    "chemicals away from people, food, and water, and consult a local "
    "agricultural extension officer for anything you are unsure about."
)


@dataclass
class OutputResult:
    text: str
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)
    appended_safety: bool = False


def scan_output(text: str, mentions_chemicals: bool | None = None) -> OutputResult:
    """Filter model output: block dangerous content, append safety note for chemical advice."""
    reasons = [p.pattern for p in _UNSAFE_RE if p.search(text or "")]
    if reasons:
        return OutputResult(
            text=(
                "I can't help with that as written because it could be unsafe. "
                "For pest or disease problems, I can suggest label-approved, "
                "safe treatments — please ask again describing the crop and symptoms."
            ),
            blocked=True,
            reasons=reasons,
        )

    if mentions_chemicals is None:
        mentions_chemicals = bool(
            re.search(r"pesticide|insecticide|fungicide|spray|dose|chemical|fertilizer",
                      text or "", re.IGNORECASE)
        )
    if mentions_chemicals and "Safety note" not in (text or ""):
        return OutputResult(text=(text or "") + _SAFETY_FOOTER, appended_safety=True)
    return OutputResult(text=text or "")


# --------------------------------------------------------------------------- #
# 4. Tool argument validation
# --------------------------------------------------------------------------- #
def validate_tool_args(tool_name: str, args: dict) -> ScanResult:
    """Reject obviously out-of-range / abusive tool arguments before execution."""
    reasons: list[str] = []
    if tool_name == "get_weather_forecast":
        lat, lon = args.get("latitude"), args.get("longitude")
        if lat is not None and not (-90 <= float(lat) <= 90):
            reasons.append("latitude out of range")
        if lon is not None and not (-180 <= float(lon) <= 180):
            reasons.append("longitude out of range")
    if tool_name == "recommend_crop":
        ph = args.get("ph")
        if ph is not None and not (0 <= float(ph) <= 14):
            reasons.append("ph out of range (0-14)")
    return ScanResult(blocked=bool(reasons), reasons=reasons)
