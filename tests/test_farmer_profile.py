"""Tests for farmer-profile session-state memory (needs google-adk for ToolContext import)."""
import pytest

pytest.importorskip("google.adk", reason="google-adk not installed")

from sprout.skills.farmer_profile import get_farmer_profile, save_farmer_profile  # noqa: E402


class _FakeCtx:
    """Minimal stand-in for ADK ToolContext (the tools only touch .state)."""

    def __init__(self):
        self.state = {}


def test_save_and_get_profile():
    ctx = _FakeCtx()
    save_farmer_profile(ctx, name="Ravi", location="Nashik", soil_type="black", crops="cotton")
    assert get_farmer_profile(ctx)["profile"]["location"] == "Nashik"


def test_save_merges_without_clobbering():
    ctx = _FakeCtx()
    save_farmer_profile(ctx, name="Ravi", soil_type="black")
    save_farmer_profile(ctx, latitude=20.0, longitude=73.8)  # should keep name+soil
    p = get_farmer_profile(ctx)["profile"]
    assert p["name"] == "Ravi" and p["soil_type"] == "black"
    assert p["latitude"] == 20.0 and p["longitude"] == 73.8


def test_empty_profile_note():
    ctx = _FakeCtx()
    out = get_farmer_profile(ctx)
    assert out["profile"] == {} and "note" in out


def test_blank_values_ignored():
    ctx = _FakeCtx()
    save_farmer_profile(ctx, name="Ravi", location="")  # blank location ignored
    assert "location" not in get_farmer_profile(ctx)["profile"]
