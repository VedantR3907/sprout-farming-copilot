# Sprout — Capstone Submission Writeup

> Paste this into the Kaggle **Writeup** for the AI Agents Vibe Coding Capstone.
> Track: **Agents for Good** (agriculture).

## 1. The problem
Over 500 million smallholder farmers grow much of the world's food, yet most lack
timely access to an agronomist, market information, or knowledge of the government
support they're entitled to. A wrong diagnosis, a bad sell decision, or a missed
subsidy can wipe out a season's income. Generic chatbots aren't enough: farming
advice must be **specialised**, **safe**, and usable by someone with limited
literacy and a basic phone.

## 2. The solution: Sprout
Sprout is a friendly **multi-agent farming co-pilot**. A coordinator agent
understands the farmer's question and hands it to the right specialist:

- **Crop Doctor** — diagnoses diseases/pests from described symptoms and gives
  organic-first, label-safe remedies.
- **Field Advisor** — live weather, mandi prices with sell/hold hints, soil
  guidance, **data-driven crop recommendation from a real dataset**, and water-wise
  irrigation plans.
- **Scheme Navigator** — finds relevant government schemes (income, credit,
  insurance, irrigation, organic, market) with eligibility and how to apply.

## 3. Key concepts demonstrated (4 of the required 3+)
1. **Multi-agent system with Google ADK** — a root orchestrator delegates to three
   specialist `LlmAgent`s via ADK's `sub_agents` transfer mechanism.
2. **Custom MCP server** — a FastMCP server exposes four agronomy tools over stdio,
   consumed by ADK's `McpToolset`. One tool calls the **live Open-Meteo API**;
   another runs **k-NN over a real 2,200-row crop dataset**.
3. **Agent skills** — three reusable, declaratively-described (`AgentSkill`)
   capability modules: `diagnose_crop`, `plan_irrigation`, `find_schemes`.
4. **Security features** — ADK callbacks on every agent: PII redaction,
   prompt-injection/jailbreak blocking, unsafe-advice filtering, and tool-argument
   validation.

## 4. Why it stands out
- **Real data, not toy data**: a vendored Kaggle/Hugging Face crop dataset (22
  crops) drives recommendations; weather is live and free.
- **Security is first-class and tested**, not an afterthought — sensitive farmer data
  (phone, Aadhaar, email) never reaches the model, and dangerous chemical advice is
  blocked with a safety note enforced.
- **Engineering quality**: clean separation of pure logic vs. framework plumbing, a
  reusable MCP server, and **28 deterministic offline tests** that run with no API key.
- **Genuinely free & reproducible**: open-source ADK, Gemini free tier, no paid APIs.

## 5. Responsible AI
Sprout gives organic remedies first, always appends a safety note to chemical
advice, refuses banned/dangerous substances and self-harm content, and reminds
farmers to verify schemes on official portals and never share OTPs. It positions
itself as a helper, not a replacement for local extension officers.

## 6. How to run / reproduce
- Code: `<your GitHub repo link>`
- `pip install -r requirements.txt`, add a free Gemini key to `.env`, then
  `python -m demo.cli --demo` or `adk web .`.
- Offline verification: `pytest -q` (28 passing).

## 7. Tech stack
Google ADK · Gemini (free tier) · Model Context Protocol (FastMCP) · Open-Meteo ·
Python 3.12 · pytest.

## 8. Future work
Add image-based disease detection (PlantVillage CNN), local-language voice I/O,
WhatsApp/IVR delivery, and a live mandi-price + scheme feed.
