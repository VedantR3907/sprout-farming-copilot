"""Multimodal demo: send a plant PHOTO to Sprout and get a diagnosis.

Sprout's crop_doctor is vision-capable (Gemini). This sends a real diseased-leaf
image to the agent, which identifies the problem from the picture and then uses
the `diagnose_crop` skill to attach organic + chemical remedies.

Usage:
    python -m demo.image_demo [path/to/leaf.jpg]

Defaults to the bundled sample (a real PlantVillage tomato early-blight leaf).
Requires GOOGLE_API_KEY in your .env (free Gemini tier).
"""
from __future__ import annotations

import asyncio
import sys
import warnings
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

warnings.filterwarnings("ignore")

from sprout.config import HAS_API_KEY, PACKAGE_DIR  # noqa: E402

DEFAULT_IMAGE = PACKAGE_DIR / "data" / "sample_images" / "tomato_early_blight.jpg"
APP, USER = "sprout", "farmer"


async def run(image_path: Path) -> None:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from sprout import root_agent

    data = image_path.read_bytes()
    message = types.Content(
        role="user",
        parts=[
            types.Part(text="Here is a photo of my plant. What is wrong and what should I do?"),
            types.Part.from_bytes(data=data, mime_type="image/jpeg"),
        ],
    )

    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)

    print(f"📷 Sending image: {image_path.name} ({len(data)} bytes)\n")
    final, author = "", ""
    async for event in runner.run_async(user_id=USER, session_id=session.id, new_message=message):
        if getattr(event, "author", None):
            author = event.author
        if event.is_final_response() and event.content and event.content.parts:
            final = "".join(p.text for p in event.content.parts if getattr(p, "text", None))
    print(f"[handled by: {author}]\nSprout: {final}")


def main() -> None:
    if not HAS_API_KEY:
        print("⚠️  Set GOOGLE_API_KEY in .env first (free: https://aistudio.google.com/apikey)")
        sys.exit(1)
    image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IMAGE
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        sys.exit(1)
    asyncio.run(run(image_path))


if __name__ == "__main__":
    main()
