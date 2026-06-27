# Sprout — ADK Evaluation Suite

This demonstrates the **agent evaluation** concept from the course using ADK's
built-in evaluation framework.

## Files
- `sprout.evalset.json` — an `EvalSet` of `EvalCase`s (built with ADK's own
  pydantic models, so it is schema-valid for this ADK version).
- `test_config.json` — pass/fail criteria (auto-discovered next to the evalset).
- `run_eval.py` — convenience runner.

## What it checks
Each case is scored on two axes:
- **`tool_trajectory_avg_score`** — did the agents call the *right tools in the
  right order*? Here: did the root `transfer_to_agent` to `field_advisor`, then
  call the correct **MCP tool** (`get_market_prices`, `get_soil_recommendation`)?
- **`response_match_score`** — ROUGE overlap of the answer with a reference.

### Why these cases
Trajectory evaluation requires **deterministic tool arguments** to be meaningful.
`field_advisor`'s MCP tools take stable string args (`crop="cotton"`,
`soil_type="sandy"`), so their trajectories reproduce exactly. The
`crop_doctor` and `scheme_navigator` tools take *free-text* args (symptom
descriptions, scheme "need") that the LLM phrases differently each run, so their
routing is covered by the **unit tests** (`tests/`) and the **live demo**
(`demo/cli.py`) instead — the appropriate tool for non-deterministic args.

## Run it
```bash
# needs GOOGLE_API_KEY in .env (free Gemini tier)
python -m eval.run_eval
# or via the ADK CLI:
adk eval sprout eval/sprout.evalset.json --config_file_path eval/test_config.json
```

## Status / notes
- The harness is verified to execute and score; the **market-price routing case
  passes `tool_trajectory_avg_score`** (the root correctly transfers to
  `field_advisor` and calls `get_market_prices(crop="cotton")` — confirmed via a
  captured live trajectory).
- ⚠️ **Free-tier quota:** Gemini's free tier on a new project can be as low as
  **20 requests/day per model**. A full eval makes several model calls, so run it
  on a fresh daily quota (or a key with higher limits). If you hit HTTP 429, wait
  for the daily reset or switch `SPROUT_MODEL` to another free model.
- Requires the eval extras: `pip install "google-adk[eval]"`.
