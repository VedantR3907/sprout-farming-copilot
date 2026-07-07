"""Core tool logic for the Sprout MCP server.

These are plain, synchronous, side-effect-light functions so they can be unit
tested offline. ``server.py`` wraps them as MCP tools exposed over stdio.

Tools:
  * get_weather_forecast  -> live data from the free Open-Meteo API (no key)
  * get_market_prices     -> curated mandi price dataset
  * get_soil_recommendation -> simple agronomy rules engine
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

# Free public sample key for data.gov.in (rate-limited). Users can set their own
# higher-limit key via the DATA_GOV_API_KEY env var (free at https://data.gov.in).
_DATA_GOV_KEY = os.getenv(
    "DATA_GOV_API_KEY", "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
)
_MANDI_RESOURCE = "9ef84268-d588-465a-a308-a864a43d0070"
_MANDI_URL = f"https://api.data.gov.in/resource/{_MANDI_RESOURCE}"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog", 51: "light drizzle", 53: "drizzle",
    55: "dense drizzle", 61: "slight rain", 63: "rain", 65: "heavy rain",
    71: "slight snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "moderate showers", 82: "violent showers", 95: "thunderstorm",
    96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


def get_weather_forecast(latitude: float, longitude: float, days: int = 3) -> dict[str, Any]:
    """Return a short daily forecast for a location using Open-Meteo (free, no key).

    Args:
        latitude: degrees, -90..90
        longitude: degrees, -180..180
        days: number of forecast days (1..7)
    """
    if not (-90 <= latitude <= 90):
        return {"error": f"latitude {latitude} out of range (-90..90)"}
    if not (-180 <= longitude <= 180):
        return {"error": f"longitude {longitude} out of range (-180..180)"}
    days = max(1, min(int(days), 7))

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "forecast_days": days,
        "timezone": "auto",
    }
    try:
        resp = httpx.get(url, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # network / API failure -> graceful, informative
        return {
            "error": "weather service unavailable",
            "detail": str(exc),
            "hint": "Check connectivity; advice can still be given without live weather.",
        }

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    out_days = []
    for i, date in enumerate(dates):
        code = (daily.get("weather_code") or [None])[i] if i < len(daily.get("weather_code", [])) else None
        out_days.append({
            "date": date,
            "condition": WEATHER_CODES.get(code, "unknown"),
            "temp_max_c": _safe_idx(daily.get("temperature_2m_max"), i),
            "temp_min_c": _safe_idx(daily.get("temperature_2m_min"), i),
            "precip_mm": _safe_idx(daily.get("precipitation_sum"), i),
            "rain_chance_pct": _safe_idx(daily.get("precipitation_probability_max"), i),
        })

    total_rain = sum(d["precip_mm"] or 0 for d in out_days)
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "days": out_days,
        "summary": _weather_summary(out_days, total_rain),
        "source": "open-meteo.com (free)",
    }


def _safe_idx(seq: list | None, i: int) -> Any:
    if seq and i < len(seq):
        return seq[i]
    return None


def _weather_summary(out_days: list[dict], total_rain: float) -> str:
    if not out_days:
        return "No forecast data available."
    if total_rain >= 25:
        return f"Significant rain expected (~{total_rain:.0f} mm). Delay irrigation and spraying."
    if total_rain >= 5:
        return f"Some rain expected (~{total_rain:.0f} mm). Light irrigation may suffice."
    return f"Mostly dry (~{total_rain:.0f} mm). Plan irrigation as needed."


def _load_market() -> dict:
    with open(DATA_DIR / "market_prices.json", encoding="utf-8") as fh:
        return json.load(fh)


def get_market_prices(crop: str) -> dict[str, Any]:
    """Return recent modal/min/max market price for a crop (INR/quintal)."""
    market = _load_market()
    key = (crop or "").strip().lower()
    crops = market.get("crops", {})
    if key in crops:
        info = crops[key]
        return {
            "crop": key,
            "currency": market.get("currency"),
            "as_of": market.get("as_of"),
            "modal_price": info["modal"],
            "min_price": info["min"],
            "max_price": info["max"],
            "trend": info["trend"],
            "advice": _price_advice(info),
        }
    return {
        "error": f"No price data for '{crop}'.",
        "available_crops": sorted(crops.keys()),
    }


def _price_advice(info: dict) -> str:
    trend = info.get("trend")
    if trend == "rising":
        return "Prices trending up — holding stock briefly may pay off if storage is safe."
    if trend == "falling":
        return "Prices trending down — selling sooner may be wiser."
    if trend == "volatile":
        return "Prices are volatile — sell in smaller lots to average out risk."
    return "Prices are stable — sell based on your cash-flow needs."


def get_live_mandi_price(commodity: str, state: str = "") -> dict[str, Any]:
    """Fetch LIVE mandi prices from data.gov.in (Agmarknet), with offline fallback.

    Returns recent real market records (INR/quintal) for a commodity, optionally
    filtered by state. If the live API is unavailable or has no record today
    (e.g. off-season), it falls back to the curated dataset so the agent can
    still answer.
    """
    commodity_key = (commodity or "").strip()
    if not commodity_key:
        return {"error": "Please name a commodity (e.g. wheat, onion, tomato)."}

    params = {
        "api-key": _DATA_GOV_KEY,
        "format": "json",
        "limit": 50,
        "filters[commodity]": commodity_key.title(),
    }
    if state and state.strip():
        params["filters[state]"] = state.strip().title()

    records: list[dict] = []
    try:
        resp = httpx.get(_MANDI_URL, params=params, timeout=4.0)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        # Retry without the state filter if nothing matched in that state.
        if not records and state:
            params.pop("filters[state]", None)
            resp = httpx.get(_MANDI_URL, params=params, timeout=4.0)
            resp.raise_for_status()
            records = resp.json().get("records", [])
    except Exception as exc:
        fb = get_market_prices(commodity_key)
        fb["source"] = "curated fallback (live API unavailable)"
        fb["detail"] = str(exc)
        return fb

    if not records:
        fb = get_market_prices(commodity_key)
        fb["source"] = "curated fallback (no live record today — may be off-season)"
        return fb

    modal_prices = [int(r["modal_price"]) for r in records if str(r.get("modal_price", "")).isdigit()]
    min_prices = [int(r["min_price"]) for r in records if str(r.get("min_price", "")).isdigit()]
    max_prices = [int(r["max_price"]) for r in records if str(r.get("max_price", "")).isdigit()]
    sample = [
        {
            "market": f"{r.get('market')}, {r.get('state')}",
            "modal_price": r.get("modal_price"),
            "date": r.get("arrival_date"),
        }
        for r in records[:5]
    ]
    return {
        "commodity": commodity_key,
        "currency": "INR/quintal",
        "records_found": len(records),
        "as_of": records[0].get("arrival_date"),
        "modal_price": round(statistics.median(modal_prices)) if modal_prices else None,
        "min_price": min(min_prices) if min_prices else None,
        "max_price": max(max_prices) if max_prices else None,
        "sample_markets": sample,
        "source": "data.gov.in / Agmarknet (live)",
        "advice": "Compare nearby markets and sell where the modal price is highest, "
        "accounting for transport cost.",
    }


# Minimal agronomy rules. Keys are (crop) -> preferences; soil adjustments layered on top.
_CROP_NEEDS = {
    "wheat": {"ph": "6.0-7.5", "water": "moderate", "n": "high", "season": "Rabi"},
    "rice": {"ph": "5.5-6.5", "water": "high", "n": "high", "season": "Kharif"},
    "paddy": {"ph": "5.5-6.5", "water": "high", "n": "high", "season": "Kharif"},
    "maize": {"ph": "5.8-7.0", "water": "moderate", "n": "high", "season": "Kharif/Rabi"},
    "cotton": {"ph": "6.0-7.5", "water": "moderate", "n": "moderate", "season": "Kharif"},
    "tomato": {"ph": "6.0-6.8", "water": "moderate", "n": "moderate", "season": "Rabi"},
    "potato": {"ph": "5.0-6.5", "water": "moderate", "n": "high", "season": "Rabi"},
    "soybean": {"ph": "6.0-7.0", "water": "moderate", "n": "low", "season": "Kharif"},
}

_SOIL_TIPS = {
    "sandy": "Drains fast and holds few nutrients — irrigate little-and-often and add compost/organic matter.",
    "clay": "Holds water and can waterlog — improve drainage, avoid over-irrigation, add organic matter to loosen.",
    "loam": "Well balanced — ideal for most crops; maintain organic matter and rotate crops.",
    "black": "High moisture retention (good for cotton) — avoid overwatering; manage cracking in dry spells.",
    "red": "Often low in nitrogen and organic matter — add manure and use balanced fertilizer.",
    "silt": "Fertile but can compact — avoid working when wet; add organic matter for structure.",
}


def get_soil_recommendation(crop: str, soil_type: str) -> dict[str, Any]:
    """Return crop+soil suitability notes and basic input guidance."""
    crop_key = (crop or "").strip().lower()
    soil_key = (soil_type or "").strip().lower()
    needs = _CROP_NEEDS.get(crop_key)
    soil_tip = _SOIL_TIPS.get(soil_key)

    result: dict[str, Any] = {"crop": crop_key, "soil_type": soil_key}
    if not needs and not soil_tip:
        result["error"] = "Unknown crop and soil type."
        result["known_crops"] = sorted(_CROP_NEEDS.keys())
        result["known_soils"] = sorted(_SOIL_TIPS.keys())
        return result

    if needs:
        result["ideal_ph"] = needs["ph"]
        result["water_need"] = needs["water"]
        result["nitrogen_need"] = needs["n"]
        result["typical_season"] = needs["season"]
    if soil_tip:
        result["soil_advice"] = soil_tip
    result["recommendation"] = _soil_reco_text(crop_key, needs, soil_key, soil_tip)
    return result


# ---------------------------------------------------------------------------
# Data-driven crop recommendation backed by a REAL dataset.
# Source: Crop Recommendation Dataset (2,200 records, 22 crops) widely mirrored
# on Kaggle / Hugging Face. Vendored as data/crop_recommendation.csv.
# We use a lightweight k-nearest-neighbours classifier (pure stdlib) over real
# soil/climate records — no heavy ML dependency required.
# ---------------------------------------------------------------------------

_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


@lru_cache(maxsize=1)
def _load_crop_dataset() -> tuple[list[dict[str, float]], list[str], dict[str, dict[str, float]]]:
    """Load the real dataset and precompute per-feature min/max for scaling."""
    rows: list[dict[str, float]] = []
    labels: list[str] = []
    path = DATA_DIR / "crop_recommendation.csv"
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                vec = {f: float(row[f]) for f in _FEATURES}
            except (KeyError, ValueError, TypeError):
                continue
            rows.append(vec)
            labels.append(row["label"].strip().lower())
    stats: dict[str, dict[str, float]] = {}
    for f in _FEATURES:
        vals = [r[f] for r in rows]
        stats[f] = {"min": min(vals), "max": max(vals)}
    return rows, labels, stats


def recommend_crop(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    top_k: int = 3,
) -> dict[str, Any]:
    """Recommend crops for given soil/climate conditions using real data (k-NN).

    Args mirror the dataset features: N/P/K (kg/ha), temperature (°C),
    humidity (%), soil pH, and rainfall (mm). Returns the most likely crops
    with a confidence share among the nearest real records.
    """
    rows, labels, stats = _load_crop_dataset()
    query = {
        "N": nitrogen, "P": phosphorus, "K": potassium,
        "temperature": temperature, "humidity": humidity,
        "ph": ph, "rainfall": rainfall,
    }

    def scaled_dist(rec: dict[str, float]) -> float:
        total = 0.0
        for f in _FEATURES:
            lo, hi = stats[f]["min"], stats[f]["max"]
            span = (hi - lo) or 1.0
            total += ((query[f] - rec[f]) / span) ** 2
        return math.sqrt(total)

    k = max(1, min(int(top_k) * 5, 25))  # vote pool
    neighbours = sorted(range(len(rows)), key=lambda i: scaled_dist(rows[i]))[:k]

    votes: dict[str, int] = {}
    for i in neighbours:
        votes[labels[i]] = votes.get(labels[i], 0) + 1
    ranked = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)[: int(top_k)]

    recommendations = [
        {"crop": crop, "confidence_pct": round(100 * count / k, 1)}
        for crop, count in ranked
    ]
    return {
        "input": query,
        "recommendations": recommendations,
        "method": "k-NN over real Crop Recommendation Dataset (2,200 records, 22 crops)",
        "source": "Kaggle/HuggingFace 'Crop Recommendation Dataset' (vendored)",
    }


def _soil_reco_text(crop, needs, soil, soil_tip) -> str:
    parts = []
    if needs:
        parts.append(
            f"{crop.title()} prefers pH {needs['ph']} with {needs['water']} water and "
            f"{needs['n']} nitrogen ({needs['season']} season)."
        )
    if soil_tip:
        parts.append(f"On {soil} soil: {soil_tip}")
    if needs and soil == "sandy" and needs["water"] == "high":
        parts.append("Note: this crop is water-hungry but sandy soil drains fast — consider drip irrigation.")
    if needs and soil == "clay" and needs["water"] == "high":
        parts.append("Good news: clay holds water well for this water-hungry crop.")
    return " ".join(parts)
