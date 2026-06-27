"""Sprout — AI Farming Co-pilot (Google ADK multi-agent system).

Importing this package exposes ``root_agent`` so ADK tooling (``adk web`` /
``adk run``) can discover it.
"""
# ADK discovers ``root_agent`` by importing this package. We import the agent
# module lazily/defensively so that the pure-logic subpackages (skills, security,
# mcp_server tools) remain importable for offline unit tests even when the
# optional ``google-adk`` dependency is not installed.
try:  # pragma: no cover - exercised only when google-adk is installed
    from sprout import agent  # noqa: F401  (re-exported for ADK discovery)

    root_agent = agent.root_agent
    __all__ = ["agent", "root_agent"]
except ImportError:  # google-adk not installed (e.g. offline test runs)
    __all__ = []
