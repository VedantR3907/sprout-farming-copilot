"""Run the ADK evaluation suite for Sprout.

Evaluates the multi-agent system against `eval/sprout.evalset.json` on two axes:
  * tool_trajectory_avg_score — did agents call the right tools?
  * response_match_score      — did the answer roughly match the reference?

Criteria live in `eval/test_config.json` (auto-discovered next to the evalset).

Usage:
    python -m eval.run_eval            # needs GOOGLE_API_KEY (free Gemini tier)

Or use the ADK CLI directly:
    adk eval sprout eval/sprout.evalset.json --config_file_path eval/test_config.json
"""
from __future__ import annotations

import asyncio
import inspect
import sys
import warnings

# ADK's result printer emits unicode (e.g. ₹); Windows cp1252 consoles choke on it.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

warnings.filterwarnings("ignore")

from sprout.config import HAS_API_KEY  # noqa: E402

EVALSET = "eval/sprout.evalset.json"


def run() -> None:
    if not HAS_API_KEY:
        raise SystemExit(
            "Set GOOGLE_API_KEY in .env first (free: https://aistudio.google.com/apikey)"
        )
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    result = AgentEvaluator.evaluate(
        agent_module="sprout",
        eval_dataset_file_path_or_dir=EVALSET,
        num_runs=1,
    )
    if inspect.isawaitable(result):
        asyncio.run(result)
    print("\n✅ Eval finished.")


if __name__ == "__main__":
    run()
