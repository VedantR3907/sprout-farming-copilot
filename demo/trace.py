"""Behind-the-scenes agent TRACE — great for the demo video.

Runs one farmer query through the multi-agent system and prints a clean,
readable trace of what happens inside:
  * which agent is active,
  * every transfer between agents,
  * every tool call (name + arguments) and its result,
  * the final answer,
  * and the TOKEN USAGE + estimated cost (it's free on the Gemini free tier).

Usage:
    python -m demo.trace                       # default: crop-disease query
    python -m demo.trace "your question here"

Requires GOOGLE_API_KEY in .env (free Gemini tier).
"""
from __future__ import annotations

import asyncio
import sys
import warnings

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

warnings.filterwarnings("ignore")

from sprout.config import HAS_API_KEY, MODEL

# Approx. Gemini 2.5 Flash paid-tier rates (USD per 1M tokens) — for illustration
# only; we run on the FREE tier (cost = $0). Verify at https://ai.google.dev/pricing
PRICE_IN_PER_M = 0.30
PRICE_OUT_PER_M = 2.50

APP, USER = "sprout", "farmer"
AGENT_EMOJI = {
    "sprout": "🧭", "crop_doctor": "🌿", "field_advisor": "🌦️", "scheme_navigator": "🏛️",
}


def _short(v, n=90):
    s = str(v)
    return s if len(s) <= n else s[: n - 1] + "…"


async def main(query: str) -> None:
    if not HAS_API_KEY:
        print("⚠️  Set GOOGLE_API_KEY in .env first (free: https://aistudio.google.com/apikey)")
        return

    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from sprout import root_agent

    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)

    print("=" * 74)
    print(f"🤖 MODEL: {MODEL}   (Google Gemini · FREE tier)")
    print(f"👤 FARMER: {query}")
    print("=" * 74)

    in_tok = out_tok = total_tok = 0
    message = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id=USER, session_id=session.id, new_message=message
    ):
        author = getattr(event, "author", "?") or "?"
        emoji = AGENT_EMOJI.get(author, "•")
        for part in (getattr(event.content, "parts", None) or []) if event.content else []:
            fc = getattr(part, "function_call", None)
            fr = getattr(part, "function_response", None)
            txt = getattr(part, "text", None)
            if fc:
                if fc.name == "transfer_to_agent":
                    tgt = (fc.args or {}).get("agent_name", "?")
                    print(f"{emoji} {author}  ──▶ transfers to  {AGENT_EMOJI.get(tgt,'•')} {tgt}")
                else:
                    print(f"{emoji} {author}  🛠  calls tool: {fc.name}({_short(dict(fc.args or {}))})")
            elif fr:
                print(f"     ↳ tool result: {_short(getattr(fr, 'response', ''))}")
            elif txt and txt.strip():
                print(f"{emoji} {author}  💬 {_short(txt.strip(), 300)}")

        um = getattr(event, "usage_metadata", None)
        if um:
            in_tok += getattr(um, "prompt_token_count", 0) or 0
            out_tok += getattr(um, "candidates_token_count", 0) or 0
            total_tok += getattr(um, "total_token_count", 0) or 0

    est = (in_tok / 1_000_000) * PRICE_IN_PER_M + (out_tok / 1_000_000) * PRICE_OUT_PER_M
    print("=" * 74)
    print(f"🔢 TOKENS  input={in_tok}  output={out_tok}  total={total_tok}")
    print(f"💰 COST    $0.00 on the free tier  (≈ ${est:.5f} even at paid rates)")
    print("=" * 74)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or (
        "My tomato leaves have brown spots with concentric rings on the lower "
        "leaves. What is it and what should I do?"
    )
    asyncio.run(main(q))
