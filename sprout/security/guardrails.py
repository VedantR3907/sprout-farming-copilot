"""ADK guardrail callbacks.

Thin adapters that plug the pure policies in ``policies.py`` into ADK's agent
lifecycle:

  * before_model_callback -> redact PII + block prompt injection (input side)
  * after_model_callback  -> block unsafe advice + append safety notes (output side)
  * before_tool_callback  -> validate tool arguments before execution

Attach all three to any agent via ``apply_guardrails(agent)``.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from sprout.security import policies

logger = logging.getLogger("sprout.security")


def _text_response(message: str) -> LlmResponse:
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=message)])
    )


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Redact PII in-place and short-circuit on injection attempts."""
    blocked_reasons: list[str] = []
    for content in getattr(llm_request, "contents", None) or []:
        if getattr(content, "role", None) not in (None, "user"):
            continue
        for part in getattr(content, "parts", None) or []:
            text = getattr(part, "text", None)
            if not text:
                continue
            # 1) injection scan
            scan = policies.scan_input(text)
            if scan.blocked:
                blocked_reasons.extend(scan.reasons)
            # 2) PII redaction (always)
            red = policies.redact_pii(text)
            if red.changed:
                part.text = red.text
                logger.info("Redacted PII: %s", red.redactions)

    if blocked_reasons:
        logger.warning("Blocked injection attempt: %s", blocked_reasons)
        # Record on session state for observability.
        try:
            callback_context.state["security_blocked_input"] = blocked_reasons
        except Exception:
            pass
        return _text_response(
            "I can only help with farming questions, and I can't follow requests "
            "to change my instructions. How can I help with your crops today? 🌱"
        )
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Block dangerous advice and append a safety note when chemicals are mentioned."""
    content = getattr(llm_response, "content", None)
    if not content or not getattr(content, "parts", None):
        return None
    # Only post-process plain text responses (skip tool-call/function parts).
    texts = [p.text for p in content.parts if getattr(p, "text", None)]
    if not texts:
        return None

    joined = "".join(texts)
    result = policies.scan_output(joined)
    if result.blocked:
        logger.warning("Blocked unsafe output: %s", result.reasons)
        return _text_response(result.text)
    if result.appended_safety:
        return _text_response(result.text)
    return None


def before_tool_callback(
    tool: BaseTool, args: dict, tool_context: ToolContext
) -> Optional[dict[str, Any]]:
    """Validate tool arguments; return an error dict to skip the call if invalid."""
    result = policies.validate_tool_args(getattr(tool, "name", ""), args or {})
    if result.blocked:
        logger.warning("Blocked tool call %s: %s", getattr(tool, "name", "?"), result.reasons)
        return {"error": "invalid arguments", "reasons": result.reasons}
    return None


def apply_guardrails(agent) -> Any:
    """Attach all three guardrail callbacks to an ADK agent and return it."""
    agent.before_model_callback = before_model_callback
    agent.after_model_callback = after_model_callback
    agent.before_tool_callback = before_tool_callback
    return agent
