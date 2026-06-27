"""Tests for the reusable agent skills (offline, no API key needed)."""
from sprout.skills import SKILLS, diagnose_crop, find_schemes, plan_irrigation


def test_diagnose_crop_matches_early_blight():
    out = diagnose_crop("brown spots with concentric rings on lower leaves", "tomato")
    names = [d["problem"] for d in out["diagnosis"]]
    assert any("Early blight" in n for n in names)
    assert out["diagnosis"][0]["organic_remedy"]
    assert "disclaimer" in out


def test_diagnose_crop_requires_symptoms():
    assert "error" in diagnose_crop("", "tomato")


def test_diagnose_crop_generic_when_no_match():
    out = diagnose_crop("the spaceship is purple", "tomato")
    assert out["diagnosis"] == [] and "message" in out


def test_plan_irrigation_skips_when_rain_enough():
    out = plan_irrigation("wheat", "loam", "vegetative", expected_rain_mm=100)
    assert "Skip irrigation" in out["action"]
    assert out["recommended_irrigation_mm"] == 0


def test_plan_irrigation_recommends_water_when_dry():
    out = plan_irrigation("rice", "sandy", "flowering", expected_rain_mm=0)
    assert out["recommended_irrigation_mm"] > 0
    assert "Sandy soil" in " ".join(out["notes"])


def test_find_schemes_loan_returns_kcc():
    out = find_schemes("I need a low interest loan for seeds")
    schemes = [m["scheme"] for m in out["matches"]]
    assert any("Kisan Credit Card" in s for s in schemes)


def test_find_schemes_insurance_returns_pmfby():
    out = find_schemes("crop insurance against drought damage")
    schemes = [m["scheme"] for m in out["matches"]]
    assert any("PMFBY" in s for s in schemes)


def test_skill_registry_complete():
    assert {"diagnose_crop", "plan_irrigation", "find_schemes"} <= set(SKILLS)
    for skill in SKILLS.values():
        assert skill.name and skill.description and skill.examples and callable(skill.fn)
