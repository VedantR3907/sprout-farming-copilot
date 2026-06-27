"""Skill: plan_irrigation.

Produces a simple, water-wise irrigation recommendation from crop water need,
soil type, growth stage, expected rainfall, and days since last watering.

Pure function — deterministic and unit-testable.
"""
from __future__ import annotations

from typing import Any

# Baseline weekly water need (mm) by crop water class.
_WATER_NEED = {"low": 20, "moderate": 35, "high": 55}

_CROP_WATER_CLASS = {
    "wheat": "moderate", "rice": "high", "paddy": "high", "maize": "moderate",
    "cotton": "moderate", "tomato": "moderate", "potato": "moderate",
    "soybean": "moderate", "sugarcane": "high", "groundnut": "moderate",
    "banana": "high", "onion": "moderate", "chickpea": "low",
}

# Soil affects irrigation frequency and retention.
_SOIL_FACTOR = {
    "sandy": {"retention": 0.6, "frequency": "little and often (every 2-3 days)"},
    "red": {"retention": 0.7, "frequency": "every 3-4 days"},
    "silt": {"retention": 0.9, "frequency": "every 4-5 days"},
    "loam": {"retention": 1.0, "frequency": "every 5-6 days"},
    "clay": {"retention": 1.2, "frequency": "less often (every 6-8 days)"},
    "black": {"retention": 1.2, "frequency": "less often (every 6-8 days)"},
}

# Growth stage multiplier on water demand.
_STAGE_FACTOR = {
    "germination": 0.5, "seedling": 0.6, "vegetative": 1.0,
    "flowering": 1.2, "fruiting": 1.1, "maturity": 0.6,
}


def plan_irrigation(
    crop: str,
    soil_type: str = "loam",
    growth_stage: str = "vegetative",
    expected_rain_mm: float = 0.0,
    days_since_last_irrigation: int = 0,
) -> dict[str, Any]:
    """Recommend whether/how much to irrigate this week.

    Args:
        crop: Crop name.
        soil_type: sandy, red, silt, loam, clay, or black.
        growth_stage: germination, seedling, vegetative, flowering, fruiting, maturity.
        expected_rain_mm: Forecast rainfall over the coming week (mm).
        days_since_last_irrigation: Days since the field was last watered.
    """
    crop_key = (crop or "").strip().lower()
    soil_key = (soil_type or "loam").strip().lower()
    stage_key = (growth_stage or "vegetative").strip().lower()

    water_class = _CROP_WATER_CLASS.get(crop_key, "moderate")
    base_need = _WATER_NEED[water_class]
    stage_mult = _STAGE_FACTOR.get(stage_key, 1.0)
    soil = _SOIL_FACTOR.get(soil_key, _SOIL_FACTOR["loam"])

    weekly_need = base_need * stage_mult
    net_need = max(0.0, weekly_need - max(0.0, expected_rain_mm))

    if expected_rain_mm >= weekly_need:
        action = "Skip irrigation this week — rainfall should cover the crop's needs."
    elif net_need < 5:
        action = "Minimal irrigation needed; monitor soil moisture."
    else:
        action = (
            f"Apply about {net_need:.0f} mm this week, split across waterings, "
            f"{soil['frequency']}."
        )

    notes = []
    if soil_key == "sandy":
        notes.append("Sandy soil drains fast — drip/short cycles reduce waste.")
    if expected_rain_mm >= 25:
        notes.append("Heavy rain expected — ensure drainage to avoid waterlogging.")
    if days_since_last_irrigation >= 7 and net_need >= 5:
        notes.append("It has been a week+ since last watering — prioritise irrigating soon.")

    return {
        "crop": crop_key,
        "soil_type": soil_key,
        "growth_stage": stage_key,
        "weekly_water_need_mm": round(weekly_need, 1),
        "expected_rain_mm": round(float(expected_rain_mm), 1),
        "recommended_irrigation_mm": round(net_need, 1),
        "schedule": soil["frequency"],
        "action": action,
        "notes": notes,
        "tip": "Water early morning or evening to cut evaporation losses.",
    }
