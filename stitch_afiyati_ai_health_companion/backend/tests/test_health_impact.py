from __future__ import annotations

from pathlib import Path

from app.services.health_impact_service import HealthImpactService


ROOT_DIR = Path(__file__).resolve().parents[2]


def assess(name_ar: str, conditions: list[str], *, amount_provided: bool = False, mixed: bool = False):
    service = HealthImpactService(ROOT_DIR)
    return service.assess(
        {
            "entries": [
                {
                    "name_ar": name_ar,
                    "category": "mixed_dish" if mixed else "beverage",
                    "requires_ingredients": mixed,
                    "amount_g": 200 if amount_provided else 100,
                    "amount_provided": amount_provided,
                }
            ]
        },
        conditions,
    )[0]


def test_diabetes_sweetened_drink_asks_for_quantity_and_cites_sources():
    result = assess("مشروب كولا", ["type_2_diabetes"])
    assessment = result["assessments"][0]

    assert result["meal_groups"][0]["id"] == "caffeinated_drink"
    assert assessment["action"] == "ask_quantity"
    assert assessment["question"] == "ما كمية «مشروب كولا» التي تناولتها؟"
    assert {source["organization"] for source in assessment["sources"]} >= {
        "National Institute for Health and Care Excellence (NICE)",
        "American Diabetes Association",
        "World Health Organization",
    }


def test_hypertension_caffeine_rule_reduces_only_after_quantity_is_known():
    result = assess("قهوة سوداء", ["hypertension"], amount_provided=True)
    assessment = result["assessments"][0]

    assert assessment["action"] == "reduce"
    assert assessment["question"] is None
    assert assessment["sources"][0]["section"] == "1.4.4"


def test_reviewed_diabetes_food_can_explicitly_show_no_documented_harm():
    result = assess("موز", ["type_2_diabetes"], amount_provided=True)
    assessment = result["assessments"][0]

    assert assessment["action"] == "no_documented_harm"
    assert "لا توجد أضرار خاصة موثقة" in assessment["assessment"]
    assert assessment["sources"]


def test_unreviewed_food_never_gets_a_false_safe_label():
    result = assess("كولا دايت", ["type_2_diabetes"], amount_provided=True)
    assessment = result["assessments"][0]

    assert assessment["action"] == "insufficient_evidence"
    assert assessment["sources"] == []


def test_mixed_dish_requires_ingredients_for_every_registered_condition():
    result = assess("كشري", ["hypertension", "type_2_diabetes"], mixed=True)

    assert result["requires_ingredients"] is True
    assert {item["condition"] for item in result["assessments"]} == {
        "hypertension",
        "type_2_diabetes",
    }
    assert {item["action"] for item in result["assessments"]} == {"needs_ingredients"}


def test_catalog_exposes_medical_sources_and_activity_json():
    catalog = HealthImpactService(ROOT_DIR).catalog()

    assert len(catalog["medical_sources"]) >= 5
    assert {activity["id"] for activity in catalog["activities"]} >= {
        "walking",
        "moderate_aerobic",
        "resistance_training",
    }
