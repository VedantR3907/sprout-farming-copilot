"""Central configuration for Sprout.

Everything tunable lives here so the rest of the codebase stays clean and the
project runs entirely on free resources.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv optional at runtime
    pass

# Project paths
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
DATA_DIR = PACKAGE_DIR / "data"
MCP_SERVER_PATH = PACKAGE_DIR / "mcp_server" / "server.py"

# Model — free-tier friendly Gemini default, overridable via env.
MODEL = os.getenv("SPROUT_MODEL", "gemini-2.0-flash")

# Whether a usable Gemini key is configured. Skills/MCP/security all work
# offline; only the LLM agents need this.
HAS_API_KEY = bool(os.getenv("GOOGLE_API_KEY")) and (
    os.getenv("GOOGLE_API_KEY") != "paste-your-free-gemini-key-here"
)

# A friendly, safety-first persona shared across agents.
GLOBAL_SAFETY_NOTE = (
    "You are Sprout, a friendly farming co-pilot for smallholder farmers. "
    "Give clear, practical, low-cost advice. Use simple language. "
    "Never recommend unsafe pesticide misuse, banned chemicals, or dosages "
    "beyond label instructions. For anything involving human health, legal, or "
    "financial risk, add a short caution and suggest consulting a local expert."
)
