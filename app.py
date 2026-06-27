"""Sprout — web UI (Gradio).

A farmer-friendly chat interface for the Sprout multi-agent system. Supports
typing **and** uploading a photo of a sick plant, shows which specialist agent
answered, and keeps per-session memory (so the farmer's location/soil/crops are
remembered within a conversation).

Run locally:
    python app.py            # then open the printed local URL

Deploy free on Hugging Face Spaces (SDK: gradio) — set GOOGLE_API_KEY as a Space
secret. See docs/DEPLOY.md.
"""
from __future__ import annotations

import mimetypes
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import gradio as gr

from sprout.config import HAS_API_KEY, MODEL, PACKAGE_DIR

APP, USER = "sprout", "farmer"
SAMPLE_IMAGE = PACKAGE_DIR / "data" / "sample_images" / "tomato_early_blight.jpg"

# Friendly labels for the answering specialist.
AGENT_LABEL = {
    "sprout": "🌱 Sprout",
    "crop_doctor": "🌿 Crop Doctor",
    "field_advisor": "🌦️ Field Advisor",
    "scheme_navigator": "🏛️ Scheme Navigator",
}

_runner = None


def _get_runner():
    """Create the ADK runner lazily (only needs the API key at call time)."""
    global _runner
    if _runner is None:
        from google.adk.runners import InMemoryRunner

        from sprout import root_agent

        _runner = InMemoryRunner(agent=root_agent, app_name=APP)
    return _runner


async def _ensure_session(session_id):
    runner = _get_runner()
    if not session_id:
        s = await runner.session_service.create_session(app_name=APP, user_id=USER)
        session_id = s.id
    return runner, session_id


async def respond(message: dict, history: list, session_id):
    """Handle one farmer turn (text and/or an uploaded image)."""
    text = (message or {}).get("text", "") or ""
    files = (message or {}).get("files", []) or []

    # Build the chat display for the user's turn.
    shown = text if text else ""
    if files:
        shown = (shown + "  \n📷 _(photo attached)_").strip()
    history = history + [{"role": "user", "content": shown or "📷 _(photo attached)_"}]

    if not HAS_API_KEY:
        history.append({
            "role": "assistant",
            "content": (
                "⚠️ No Gemini API key configured. Set `GOOGLE_API_KEY` (free from "
                "https://aistudio.google.com/apikey) to chat live. Meanwhile, the "
                "skills, MCP tools, and security layer all work offline — see the repo."
            ),
        })
        return history, session_id, None

    from google.genai import types

    parts = []
    if text:
        parts.append(types.Part(text=text))
    for f in files:
        try:
            data = Path(f).read_bytes()
            mime = mimetypes.guess_type(f)[0] or "image/jpeg"
            parts.append(types.Part.from_bytes(data=data, mime_type=mime))
        except Exception:
            pass
    if not parts:
        return history, session_id, None

    runner, session_id = await _ensure_session(session_id)

    final, author = "", ""
    try:
        async for event in runner.run_async(
            user_id=USER,
            session_id=session_id,
            new_message=types.Content(role="user", parts=parts),
        ):
            if getattr(event, "author", None):
                author = event.author
            if event.is_final_response() and event.content and event.content.parts:
                final = "".join(
                    p.text for p in event.content.parts if getattr(p, "text", None)
                )
    except Exception as exc:
        msg = str(exc)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            final = (
                "⚠️ The free Gemini quota for today is used up (the free tier allows "
                "only a few requests/day). Please try again later or use a key with "
                "higher limits."
            )
        else:
            final = f"Sorry, something went wrong: {msg[:200]}"

    label = AGENT_LABEL.get(author, "🌱 Sprout")
    history.append({"role": "assistant", "content": f"**{label}**\n\n{final or '(no response)'}"})
    return history, session_id, None


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Sprout — AI Farming Co-pilot", theme=gr.themes.Soft(
        primary_hue="green", secondary_hue="emerald")) as demo:
        gr.Markdown(
            "# 🌱 Sprout — AI Farming Co-pilot\n"
            "Your pocket **agronomist + market analyst + government-scheme advisor**, "
            "built on Google's Agent Development Kit. Ask about crop diseases, what to "
            "grow, market prices, irrigation, or government schemes — in your own "
            "language. You can also **upload a photo** of a sick plant. 🌾"
        )
        session_id = gr.State(None)
        chatbot = gr.Chatbot(
            height=460,
            label="Chat with Sprout",
            value=[{
                "role": "assistant",
                "content": "**🌱 Sprout**\n\nNamaste! 🙏 I'm Sprout. Tell me about your "
                "crop — or upload a photo of a sick plant — and I'll help. "
                "Try one of the examples below.",
            }],
        )
        box = gr.MultimodalTextbox(
            interactive=True,
            file_types=["image"],
            placeholder="Type your question (any language) or attach a plant photo…",
            show_label=False,
        )
        with gr.Row():
            gr.Examples(
                examples=[
                    {"text": "My tomato leaves have brown spots with rings. What is it?", "files": []},
                    {"text": "Soil: N 90, P 42, K 43, pH 6.5, 21C, 82% humidity, 200mm rain. What should I grow?", "files": []},
                    {"text": "What is today's market price for onion in Maharashtra?", "files": []},
                    {"text": "I need a low-interest loan to buy seeds. Any govt scheme?", "files": []},
                    {"text": "मेरी गेहूँ की फसल को कितना पानी देना चाहिए?", "files": []},
                ],
                inputs=box,
                label="Examples (click to try)",
            )
        if SAMPLE_IMAGE.exists():
            gr.Markdown(
                f"💡 Tip: try the multimodal feature — upload a leaf photo. A sample "
                f"diseased-leaf image ships in the repo at `{SAMPLE_IMAGE.relative_to(PACKAGE_DIR.parent)}`."
            )
        gr.Markdown(
            f"<sub>Model: {MODEL} · Free Gemini tier · "
            "Educational guidance only — follow product labels and consult a local "
            "agricultural expert. Sprout redacts personal info and refuses unsafe advice.</sub>"
        )

        box.submit(respond, [box, chatbot, session_id], [chatbot, session_id, box])
    return demo


demo = build_demo()

if __name__ == "__main__":
    demo.launch()
