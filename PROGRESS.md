# PROGRESS / HANDOFF LOG — Sprout 🌱

> This file is the single source of truth for the build state so any agent (or human)
> can pick the project up mid-stream. Update it after every meaningful change.

## Project at a glance
- **Name:** Sprout — AI Farming Co-pilot for smallholder farmers
- **Competition:** Kaggle "AI Agents: Intensive Vibe Coding Capstone Project"
- **Track:** Agents for Good (agriculture)
- **Goal:** Best-in-track project demonstrating 4 required concepts (only 3 needed):
  1. Multi-agent system with **Google ADK** (root orchestrator + 3 sub-agents)
  2. Custom **MCP server** (weather / market / soil tools, consumed via ADK `McpToolset`)
  3. **Agent skills** (reusable, manifest-described capability modules)
  4. **Security features** (PII redaction, prompt-injection block, unsafe-advice filter, tool-arg validation)
- **Cost:** 100% free. Gemini free tier (AI Studio API key) + Open-Meteo (no key) + open-source libs.

## Tech / versions (verified 2026-06-27)
- Python 3.12.3, pip 24.0, git 2.54 (Windows)
- `google-adk` (pip), model `gemini-2.0-flash` (free tier; configurable via env)
- MCP: `mcp` library (FastMCP / lowlevel Server), ADK `McpToolset` + `StdioConnectionParams` + `StdioServerParameters`
- Env vars: `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI=FALSE`, `SPROUT_MODEL` (optional)

### Key ADK API references (confirmed from adk.dev)
```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
```

## Architecture
```
                 [ root_agent: orchestrator ]
                /            |               \
        crop_doctor    field_advisor     scheme_navigator
        (diagnose      (MCP tools:        (gov scheme
         disease/pest)  weather/market/    retrieval)
                        soil)
   skills:          skills:             skills:
   diagnose_crop    plan_irrigation     find_schemes
   ----------------------------------------------------
   security guardrails wrap every agent (before/after model + before tool)
```

## Build status (update the boxes)
- [x] Decisions locked (track, idea, stack, deliverables)
- [x] Research (Kaggle reqs, ADK/MCP APIs)
- [x] Task 1: Scaffold repo + config + logs
- [x] Task 2: MCP server (weather/market/soil)
- [x] Task 3: Agent skills package
- [x] Task 4: Security guardrails
- [x] Task 5: Multi-agent ADK wiring
- [x] Task 6: Tests, demo CLI, notebook, docs, writeup, video script

## ✅ BUILD COMPLETE (2026-06-27)
- 28/28 offline tests passing (`pytest -q`) — no API key required.
- MCP server verified end-to-end over stdio (4 tools: weather/market/soil/recommend_crop).
- Agent tree builds: root `sprout` + 3 sub-agents, guardrails on all, MCP toolset attached.
- Real dataset vendored: `sprout/data/crop_recommendation.csv` (2,200 rows, 22 crops).
- Kaggle notebook generated & validated: `notebook/sprout_capstone.ipynb` (19 cells).
- Docs done: README, ARCHITECTURE, SUBMISSION_WRITEUP, VIDEO_SCRIPT.
- git initialized + committed locally.
- google-adk 2.3.0, mcp installed in the system Python.

### ONLY remaining (needs the user — cannot be done without their key/accounts):
1. Paste a free Gemini key into `.env`, then run `python -m demo.cli --demo` to see live LLM replies.
2. Create a GitHub repo and `git remote add origin … && git push` (for the Kaggle "code link").
3. Record the ~3-min video using `docs/VIDEO_SCRIPT.md`.
4. Submit the Kaggle Writeup using `docs/SUBMISSION_WRITEUP.md`.

### Verified-untested path: live LLM conversation (no key available to this build agent).
Everything deterministic/offline IS tested. The LLM call path is standard ADK
(`InMemoryRunner.run_async`) and imports cleanly; it just needs the key to execute.

## 🔁 SESSION 2 (2026-06-27) — regression testing + enhancements (key provided)
**Live multi-agent flow VERIFIED working** with the user's Gemini key:
- Disease→crop_doctor (Early blight), recommend_crop→field_advisor (real-data MCP), scheme→scheme_navigator (KCC), injection blocked, PII redacted. ✅
- 📷 Multimodal VERIFIED: sent a real PlantVillage leaf photo → crop_doctor (Gemini Vision) correctly diagnosed Early blight + remedies. ✅

**Bug found via regression + FIXED:** input guardrail scanned the WHOLE history for
injection, so one past injection permanently blocked a session. Now scans only the
latest user message (`sprout/security/guardrails.py`). Added 4 regression tests.

**Enhancements added (project now demonstrates 5 concepts + 3 bonuses):**
- Concept 5: ADK **evaluation** suite (`eval/`: evalset + config + runner + gated test).
- 📷 Multimodal leaf-photo diagnosis (`demo/image_demo.py`, sample image vendored).
- 🧠 Session-state **memory** (`sprout/skills/farmer_profile.py`, wired into root + field_advisor).
- 🌐 **Multilingual** replies (persona in `config.py`).
- Default model switched to `gemini-2.5-flash` (2.0-flash quota was exhausted).

**Tests now: 36 passing, 1 skipped (gated live eval). `pytest -q`.**

### ⚠️ IMPORTANT quota finding (tell the user):
The provided Gemini free-tier key allows only **~20 requests/day PER MODEL**
(both gemini-2.5-flash and -flash-lite hit `RESOURCE_EXHAUSTED` after testing).
Implications:
- The ADK eval suite (`eval/run_eval.py`) is built + the harness verified to run +
  the market-price routing case passed trajectory, but a FULL green eval run needs
  a fresh daily quota or a higher-limit key. Re-run `python -m eval.run_eval` tomorrow.
- For the demo video, pace live calls (or use a second free key / new project).
- Offline tests need NO key and fully exercise skills/MCP/security/memory logic.

### Live mandi prices added (session 2b)
- New MCP tool `get_live_mandi_price(commodity, state)` → data.gov.in/Agmarknet
  (free; public sample key default, override via `DATA_GOV_API_KEY`). Verified the
  API returns real records (14k rows dated today) earlier, but it is SLOW/FLAKY and
  was timing out later — so the tool **fails fast (12s) and falls back to curated
  data**. Deterministic offline fallback test added (mocks an outage).
- field_advisor now prefers live prices; MCP server exposes 5 tools.
- Network tests are opt-in: `SPROUT_RUN_NET=1 pytest`. Default suite: **37 passed,
  3 skipped (2 net + 1 gated eval), ~3s, no key needed.**

### git: committed through session 2. `.env` (with the key) is gitignored — NEVER commit it.

## How to run (once built)
```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env            # then paste your free Gemini key
pytest -q                       # runs offline unit tests (no API key needed)
python -m demo.cli              # interactive farmer chat (needs key)
adk web sprout                  # ADK web UI (needs key)
```

## What still needs the user
- A free Gemini API key from https://aistudio.google.com/apikey (paste into `.env`)
- (Optional) GitHub repo to push to for the "code link" in the Kaggle submission
- Record the ~3 min demo video using docs/VIDEO_SCRIPT.md

## Submission checklist (Kaggle)
- [ ] Kaggle Writeup (use docs/SUBMISSION_WRITEUP.md)
- [ ] Video explanation (use docs/VIDEO_SCRIPT.md)
- [x] Link to code (GitHub repo): https://github.com/VedantR3907/sprout-farming-copilot
- [ ] Brief rationale (in writeup)

> Repo pushed 2026-06-27 over SSH (user VedantR3907, branch main). `.env` is
> gitignored and was NOT pushed — only `.env.example`. To push future changes:
> `git push` (remote `origin` already set to the SSH URL).

## Decision log
- 2026-06-27: Chose Sprout / Agents for Good (user picked). Deliverable = repo + notebook + writeup + video script (researched Kaggle reqs: writeup+video+code link).
- 2026-06-27: Designed for 4 concepts to exceed the 3-concept bar.
