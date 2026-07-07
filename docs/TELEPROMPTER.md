# 🎬 Sprout — Video Run-Sheet (record in one take, ~3 min)

## PREP (do BEFORE recording — 5 min)
- [ ] Terminal 1 (in project folder): run `python app.py` → open http://127.0.0.1:7860 → refresh tab so chat is clean
- [ ] Terminal 2 (in project folder): type `python -m demo.trace` but DON'T press Enter
- [ ] Terminal 3 (in project folder): type `pytest -q` but DON'T press Enter
- [ ] Browser tab 2: open `docs/architecture.html` (double-click the file)
- [ ] Browser tab 3: open https://github.com/VedantR3907/sprout-farming-copilot
- [ ] Know the photo path: `sprout/data/sample_images/tomato_early_blight.jpg`
- [ ] Test quota: send "hello" in the UI once. Reply = good. Refresh tab after.
- [ ] Mic on: Win+Alt+M · Start/stop recording: Win+Alt+R

---

## RECORD — actions in [brackets], read the quoted lines aloud

### 1. INTRO — 15s
[Screen: the Sprout web UI]
> "Hi, I'm Vedant. This is Sprout — an AI farming co-pilot for smallholder
> farmers. Over 500 million farming families have no easy access to an
> agronomist, market prices, or the government schemes they qualify for.
> Sprout puts all three in their pocket — for free. This is my Agents for
> Good capstone, built with Google's Agent Development Kit."

### 2. ARCHITECTURE — 25s
[Switch to the architecture.html tab, slowly move mouse down the diagram]
> "Here's the architecture. Four agents: one root orchestrator that
> understands the farmer and routes to three specialists — a Crop Doctor,
> a Field Advisor, and a Scheme Navigator. Every agent is wrapped in a
> security layer that redacts personal data, blocks prompt injection, and
> filters unsafe advice. The Field Advisor talks to my custom MCP server —
> five tools backed by live weather, live government mandi prices, and a
> real 2,200-row crop dataset. The model is Gemini 2.5 Flash on the free
> tier — this entire system costs zero to run."

### 3. DEMO 1 — disease by TEXT — 30s
[Switch to Sprout UI. Click the example: "My tomato leaves have brown spots with rings"]
> "Let's use it. A farmer describes a sick plant... The coordinator routes
> this to the Crop Doctor, which calls the diagnose skill — and there it is:
> Early Blight, with an organic remedy first, a chemical option with label
> warnings, and a prevention tip. Notice the safety note is added
> automatically — that's the guardrail layer."

### 4. DEMO 2 — disease by PHOTO — 30s
[Click 📎 in the chat box → pick tomato_early_blight.jpg → type "What is wrong with my plant?" → send]
> "But many farmers won't type symptoms — so they don't have to. I'm
> uploading an actual photo of a diseased leaf... Gemini Vision reads the
> image itself, identifies Early Blight from the picture, and pulls the same
> safe treatment plan. Photo in, diagnosis out — in any language the farmer
> speaks."

### 5. DEMO 3 — live market data — 20s
[Type: "What is the market price for onion in Maharashtra?" → send]
> "Now a money question. The Field Advisor calls the MCP server, which hits
> the Indian government's live Agmarknet price API — real mandi prices, plus
> advice on whether to sell or hold. If the API is down, it falls back to
> offline data, so the farmer always gets an answer."

### 6. BEHIND THE SCENES — trace — 25s
[Switch to Terminal 2, press Enter on `python -m demo.trace`, let it print]
> "Here's what happens under the hood. Watch the trace: the root agent
> transfers to the Crop Doctor... the Crop Doctor calls the diagnose tool
> with the symptoms... gets the result... and answers. And look at the cost
> line — about two thousand tokens, zero dollars on the free tier, and
> even at paid rates roughly six hundredths of a cent per consultation."

### 7. QUALITY — tests — 15s
[Switch to Terminal 3, press Enter on `pytest -q`]
> "It's engineered, not just prompted — thirty-seven automated tests cover
> the multi-agent routing, the MCP tools, the skills, the security policies,
> and there's an ADK evaluation suite scoring the agent's tool trajectories."

### 8. CLOSE — 15s
[Switch to the GitHub tab, scroll slowly]
> "So that's Sprout: five course concepts — multi-agent ADK, a custom MCP
> server, agent skills, security, and evaluation — plus vision, memory,
> multilingual support, and a web UI. Fully open source, fully free, built
> for the people who feed us. Thank you."

[Win+Alt+R to STOP. Video is in Videos\Captures]

---

## AFTER RECORDING → SUBMIT (in this order)

1. **Cover image**: screenshot architecture.html (Win+Shift+S), save as cover.png
2. **YouTube**: youtube.com → Create → Upload → your video →
   Title: "Sprout — AI Farming Co-pilot (Google ADK Capstone)" →
   Visibility: **Unlisted** → copy link
3. **Kaggle Writeup**: competition page → Writeups tab → **New Writeup**
   - Title: `Sprout — AI Farming Co-pilot for Smallholder Farmers`
   - Subtitle: `A multimodal multi-agent ADK system: photo crop-diagnosis, live weather & mandi prices, and government-scheme help — free, multilingual, safety-first.`
   - Body: paste from docs/SUBMISSION_WRITEUP.md, put the YouTube link in the Video section
   - **Media Gallery**: upload cover.png + add the YouTube video
   - **Project link**: https://github.com/VedantR3907/sprout-farming-copilot
   - **Track**: Agents for Good
4. Click **Save** → then the **Submit** button (top-right) → confirm.
   ⚠️ A saved draft does NOT count — you must press Submit before 12:29 PM IST.
5. Reopen the writeup page and confirm it shows as **Submitted**.

## IF SOMETHING BREAKS MID-RECORDING
- Quota 429 in the UI → narrate over the trace/tests instead (they prove it works), or use Plan B: record pytest + README + architecture only.
- Don't restart for small stumbles — judges care about content, not polish.
