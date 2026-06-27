"""Interactive / scripted demo runner for Sprout.

Usage:
    python -m demo.cli            # interactive chat (needs a Gemini API key)
    python -m demo.cli --demo     # run the canned scenarios end-to-end

Requires GOOGLE_API_KEY in your environment / .env (free from
https://aistudio.google.com/apikey).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore")

from sprout.config import HAS_API_KEY, MODEL  # noqa: E402

APP = "sprout"
USER = "farmer"


def _require_key() -> None:
    if not HAS_API_KEY:
        print(
            "\n⚠️  No Gemini API key found.\n"
            "   1) Get a FREE key: https://aistudio.google.com/apikey\n"
            "   2) Copy .env.example to .env and paste it as GOOGLE_API_KEY\n"
            "   (Skills, MCP tools, and security all work offline — run `pytest`.)\n"
        )
        sys.exit(1)


async def _run_once(runner, session_id: str, text: str) -> str:
    from google.genai import types

    message = types.Content(role="user", parts=[types.Part(text=text)])
    final = ""
    async for event in runner.run_async(
        user_id=USER, session_id=session_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final = "".join(p.text for p in event.content.parts if getattr(p, "text", None))
    return final


async def _make_runner():
    from google.adk.runners import InMemoryRunner

    from sprout import root_agent

    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    return runner


async def interactive() -> None:
    runner = await _make_runner()
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)
    print(f"🌱 Sprout is ready (model: {MODEL}). Type 'quit' to exit.\n")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in {"quit", "exit", "q"}:
            break
        if not text:
            continue
        reply = await _run_once(runner, session.id, text)
        print(f"\nSprout: {reply}\n")


async def run_demo() -> None:
    from demo.scenarios import SCENARIOS

    runner = await _make_runner()
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)
    for i, sc in enumerate(SCENARIOS, 1):
        print("=" * 78)
        print(f"[{i}] {sc['title']}")
        print(f"Farmer: {sc['query']}")
        reply = await _run_once(runner, session.id, sc["query"])
        print(f"Sprout: {reply}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sprout demo runner")
    parser.add_argument("--demo", action="store_true", help="run canned scenarios")
    args = parser.parse_args()
    _require_key()
    asyncio.run(run_demo() if args.demo else interactive())


if __name__ == "__main__":
    main()
