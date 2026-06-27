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
- [ ] Task 6: Tests, demo CLI, notebook, docs, writeup, video script (IN PROGRESS)

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
- [ ] Link to code (GitHub repo)
- [ ] Brief rationale (in writeup)

## Decision log
- 2026-06-27: Chose Sprout / Agents for Good (user picked). Deliverable = repo + notebook + writeup + video script (researched Kaggle reqs: writeup+video+code link).
- 2026-06-27: Designed for 4 concepts to exceed the 3-concept bar.
