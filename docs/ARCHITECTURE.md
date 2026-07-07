# Sprout — Architecture Deep Dive

## 1. Why multi-agent?
A smallholder farmer's questions span very different domains: plant pathology,
agronomy/economics, and bureaucracy. A single mega-prompt handling all of them is
brittle and hard to secure. Sprout instead uses an **ADK multi-agent system**: a
coordinator routes each request to a focused specialist with its own instructions
and tools. This is easier to reason about, test, extend, and secure.

```
root_agent (LlmAgent, "sprout")
 ├── crop_doctor       → tool: diagnose_crop (skill)
 ├── field_advisor     → tools: MCP toolset (4 tools) + plan_irrigation (skill)
 └── scheme_navigator  → tool: find_schemes (skill)
```

Delegation is **LLM-driven**: each sub-agent has a `description` the root uses to
decide transfers (ADK's `sub_agents` mechanism). The root also handles greetings
and clarifying questions itself.

## 2. Concept 1 — Multi-agent system (ADK)
- `sprout/agent.py` builds `root_agent` with `sub_agents=[...]`.
- Each specialist is an `LlmAgent` in `sprout/sub_agents/` with a tight instruction
  and a minimal toolset.
- ADK discovers `root_agent` because `sprout/__init__.py` re-exports it, so
  `adk web .` and `adk run sprout` work out of the box.

## 3. Concept 2 — Custom MCP server
- `sprout/mcp_server/server.py` is a **FastMCP** server exposing five tools:
  - `get_weather_forecast` → live data from **Open-Meteo** (free, no key).
  - `get_live_mandi_price` → **live** mandi prices from **data.gov.in / Agmarknet**
    (free key), with automatic fallback to curated data when the API is slow/down.
  - `get_market_prices` → curated mandi price dataset with sell/hold hints (fallback).
  - `get_soil_recommendation` → small agronomy rules engine.
  - `recommend_crop` → **k-NN over a real 2,200-row crop dataset** (22 crops).
- All tool *logic* lives in `sprout/mcp_server/tools.py` as pure functions, so it is
  unit-testable without launching a server.
- `field_advisor` consumes the server via ADK's `McpToolset` +
  `StdioConnectionParams` + `StdioServerParameters`, launching it as a subprocess
  and speaking MCP over **stdio**. Because it's a standard MCP server, any other MCP
  client (e.g. the Gemini CLI) could reuse it.

## 4. Concept 3 — Agent skills
- `sprout/skills/` holds three reusable capabilities, each a **pure function** plus a
  declarative **`AgentSkill` manifest** (`manifest.py`): id, name, description, tags,
  and example prompts.
- Skills (`diagnose_crop`, `plan_irrigation`, `find_schemes`) are independently
  testable and are attached to agents as ADK function tools. The manifest registry
  doubles as a self-documenting catalogue rendered in the README/notebook.

## 5. Concept 4 — Security features
Implemented as **pure policies** (`security/policies.py`, no ADK dependency) wired in
as **ADK callbacks** (`security/guardrails.py`) on *every* agent:

| Stage | Callback | Protection |
|-------|----------|-----------|
| Input | `before_model_callback` | Redact PII (phone/email/Aadhaar/card) **and** block prompt-injection / jailbreak |
| Output | `after_model_callback` | Block dangerous advice (banned chemicals, self-harm) and append a safety note to any chemical advice |
| Tools | `before_tool_callback` | Validate arguments (e.g., lat/long range, pH 0–14) before execution |

Separating *policy* from *plumbing* keeps the security logic fast, deterministic, and
unit-tested (see `tests/test_security.py`) independent of the model.

## 6. Data sources
- **Open-Meteo** — live weather, free, no API key.
- **data.gov.in / Agmarknet** — live daily mandi commodity prices (free key; a public
  sample key ships as the default, override with `DATA_GOV_API_KEY`).
- **Crop Recommendation Dataset** (Kaggle/Hugging Face, ~2,200 records, 22 crops) —
  vendored at `sprout/data/crop_recommendation.csv` and used by `recommend_crop`.
- **PlantVillage** — a real diseased-leaf image vendored for the multimodal demo.
- Curated JSON knowledge bases for **government schemes**, **market prices**, and
  **crop diseases** (PlantVillage-style taxonomy) — also serve as offline fallbacks.

## 7. Reliability & cost
- Network failures degrade gracefully (weather tool returns an informative error;
  advice can continue without it).
- 28 offline tests run with no API key; the only paid-tier-optional piece is the
  Gemini model, used on its free tier.

## 8. Concept 5 — Evaluation (ADK eval)
`eval/` contains an ADK `EvalSet` (`sprout.evalset.json`), pass/fail criteria
(`test_config.json`), and a runner (`run_eval.py`). It scores
**`tool_trajectory_avg_score`** (did the root transfer to `field_advisor` and call
the right **MCP** tool?) and **`response_match_score`**. Trajectory cases use
deterministic tool args (e.g. `get_market_prices(crop="cotton")`); free-text-arg
routing (crop_doctor/scheme_navigator) is covered by unit tests + the live demo.
A gated `tests/test_eval.py` (`RUN_ADK_EVAL=1`) runs it in CI when a key is present.

## 9. Bonus capabilities
- **Multimodal vision** — `crop_doctor` is a Gemini model and reads image parts.
  `demo/image_demo.py` sends a real PlantVillage leaf photo; the agent describes
  what it sees, then calls `diagnose_crop` for remedies. No extra dependency — the
  image is passed as a `types.Part.from_bytes(...)` in the user message.
- **Session-state memory** — `sprout/skills/farmer_profile.py` exposes
  `save_farmer_profile` / `get_farmer_profile` which read/write
  `tool_context.state`. ADK persists this for the session, so the farmer's
  location/soil/crops are remembered across turns and reused by `field_advisor`.
- **Multilingual** — the shared persona instructs every agent to reply in the
  farmer's own language, making Sprout usable by non-English speakers.

## 10. Extending Sprout
- Add a tool: implement a pure function in `mcp_server/tools.py`, expose it with
  `@mcp.tool()` in `server.py`.
- Add a skill: drop a pure function in `skills/`, register an `AgentSkill` in
  `manifest.py`, attach to an agent.
- Add a specialist: create an `LlmAgent` in `sub_agents/`, wrap with
  `apply_guardrails`, add to `root_agent.sub_agents`.
