"""Tests for the MCP tool logic (offline; weather test skips if no network)."""
import os

import pytest

from sprout.mcp_server import tools


def test_recommend_crop_rice_conditions():
    out = tools.recommend_crop(90, 42, 43, 21, 82, 6.5, 200)
    crops = [r["crop"] for r in out["recommendations"]]
    assert "rice" in crops
    assert out["recommendations"][0]["confidence_pct"] > 0


def test_recommend_crop_uses_real_dataset():
    rows, labels, stats = tools._load_crop_dataset()
    assert len(rows) >= 2000  # the real dataset has ~2200 records
    assert len(set(labels)) >= 20  # ~22 crops


def test_market_prices_known_crop():
    out = tools.get_market_prices("wheat")
    assert out["modal_price"] > 0
    assert out["trend"] in {"rising", "falling", "stable", "volatile"}


def test_market_prices_unknown_crop_lists_options():
    out = tools.get_market_prices("unobtainium")
    assert "error" in out and out["available_crops"]


def test_soil_recommendation_combines_crop_and_soil():
    out = tools.get_soil_recommendation("rice", "sandy")
    assert "recommendation" in out
    assert "drip irrigation" in out["recommendation"].lower()


def test_soil_recommendation_unknown():
    out = tools.get_soil_recommendation("zzz", "qqq")
    assert "error" in out


def test_weather_rejects_bad_coords():
    assert "error" in tools.get_weather_forecast(999, 0)


@pytest.mark.skipif(os.getenv("SPROUT_SKIP_NET") == "1", reason="network disabled")
def test_weather_live_or_graceful():
    """Live call to Open-Meteo; must either return days or a graceful error dict."""
    out = tools.get_weather_forecast(28.61, 77.20, days=2)  # New Delhi
    assert "days" in out or "error" in out
