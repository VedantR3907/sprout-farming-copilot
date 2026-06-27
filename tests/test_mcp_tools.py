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


# Live-network tests are opt-in (external APIs can be slow/flaky). Enable with:
#   SPROUT_RUN_NET=1 pytest
_NET = pytest.mark.skipif(
    os.getenv("SPROUT_RUN_NET") != "1", reason="set SPROUT_RUN_NET=1 for live network tests"
)


@_NET
def test_weather_live_or_graceful():
    """Live call to Open-Meteo; must either return days or a graceful error dict."""
    out = tools.get_weather_forecast(28.61, 77.20, days=2)  # New Delhi
    assert "days" in out or "error" in out


def test_live_mandi_requires_commodity():
    assert "error" in tools.get_live_mandi_price("")


def test_live_mandi_falls_back_gracefully_offline(monkeypatch):
    """If the live API errors, we must return curated data, never crash."""
    def boom(*a, **k):
        raise RuntimeError("simulated API outage")

    monkeypatch.setattr(tools.httpx, "get", boom)
    out = tools.get_live_mandi_price("onion")
    assert "fallback" in out["source"] and out["modal_price"] > 0


@_NET
def test_live_mandi_returns_data_or_fallback():
    """Live data.gov.in call; must return live records OR a curated fallback (never crash)."""
    out = tools.get_live_mandi_price("Onion")
    assert "source" in out
    assert out.get("records_found", 0) > 0 or "modal_price" in out
