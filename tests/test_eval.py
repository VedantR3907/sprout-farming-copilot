"""Gated ADK evaluation test.

Runs the live ADK eval suite ONLY when explicitly enabled, because it needs a
Gemini API key and consumes free-tier quota. Enable with:

    RUN_ADK_EVAL=1 pytest tests/test_eval.py

Normal `pytest` runs skip it so the offline suite stays free and deterministic.
"""
import os

import pytest

if os.getenv("RUN_ADK_EVAL") != "1":
    pytest.skip("set RUN_ADK_EVAL=1 to run the live ADK eval", allow_module_level=True)

pytest.importorskip("google.adk.evaluation.agent_evaluator")
pytest.importorskip("pandas", reason="install google-adk[eval]")


@pytest.mark.asyncio
async def test_sprout_eval_suite():
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    await AgentEvaluator.evaluate(
        agent_module="sprout",
        eval_dataset_file_path_or_dir="eval/sprout.evalset.json",
        num_runs=1,
    )
