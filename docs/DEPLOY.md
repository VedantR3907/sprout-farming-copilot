# Deploying Sprout's web UI (free)

The UI is a Gradio app (`app.py`). It runs locally and deploys free on Hugging
Face Spaces.

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env          # paste your free Gemini key
python app.py                 # open the printed http://127.0.0.1:7860 URL
```

## Deploy to Hugging Face Spaces (free, gives a public live link)

You'll need a free account at https://huggingface.co.

### Option A — via the website (no token needed)
1. Go to **https://huggingface.co/new-space**.
2. Name it (e.g. `sprout-farming-copilot`), **SDK: Gradio**, hardware: **CPU basic (free)**.
3. In the new Space, open **Files → add file** and upload the project, OR (easier)
   in **Settings** connect/clone — then upload these so the layout matches the repo:
   `app.py`, `requirements.txt`, and the whole `sprout/` folder (plus `demo/` is
   optional). The `sprout/` package **must** be present (the app imports it).
4. Replace the Space's auto-generated `README.md` with the contents of
   [`deploy/README_SPACE.md`](../deploy/README_SPACE.md) (keep its YAML header).
5. **Settings → Variables and secrets → New secret**: name `GOOGLE_API_KEY`,
   value = your free Gemini key. (Optional: `SPROUT_MODEL`, `DATA_GOV_API_KEY`.)
6. The Space builds and goes live at `https://huggingface.co/spaces/<you>/<name>`.

### Option B — push from your machine (git)
Hugging Face Spaces are git repos.
```bash
# 1) create an empty Gradio Space on the website first (steps 1-2 above)
# 2) then, from this project folder:
git remote add space https://huggingface.co/spaces/<your-hf-username>/sprout-farming-copilot
git push space main
# When prompted, username = your HF username, password = a HF access token
#   (create at https://huggingface.co/settings/tokens, role: write)
```
Make sure the Space's `README.md` has the YAML header from `deploy/README_SPACE.md`,
and set the `GOOGLE_API_KEY` secret in the Space settings.

## Notes
- **Quota:** the app uses the free Gemini tier (can be ~20 requests/day per model
  on a new key). It shows a friendly message when quota is exhausted.
- **No key?** The app still loads and explains how to add one; the offline parts
  (skills, MCP tools, security) work without any key — run `pytest -q`.
- The custom MCP server is launched by the app as a subprocess, so no extra
  service is needed on the Space.
