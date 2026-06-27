"""Structural tests for the multi-agent system.

These need ``google-adk`` installed (no API key required — we only build the
agent objects, we don't call the model). Skipped gracefully if ADK is absent.
"""
import warnings

import pytest

warnings.filterwarnings("ignore")

adk = pytest.importorskip("google.adk", reason="google-adk not installed")


def test_root_agent_has_three_subagents():
    import sprout

    ra = sprout.root_agent
    names = {s.name for s in ra.sub_agents}
    assert names == {"crop_doctor", "field_advisor", "scheme_navigator"}


def test_all_agents_have_guardrails():
    import sprout

    agents = [sprout.root_agent, *sprout.root_agent.sub_agents]
    for a in agents:
        assert a.before_model_callback is not None
        assert a.after_model_callback is not None
        assert a.before_tool_callback is not None


def test_field_advisor_has_mcp_toolset():
    import sprout

    fa = next(s for s in sprout.root_agent.sub_agents if s.name == "field_advisor")
    tool_types = {type(t).__name__ for t in fa.tools}
    assert "McpToolset" in tool_types
