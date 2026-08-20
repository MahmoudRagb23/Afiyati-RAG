from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
from openpyxl import Workbook

from app.core.config import Settings
from app.db.database import Database
from app.services.cofid_service import CoFIDProvider
from app.services.food_data_service import FoodDataService


def build_service(tmp_path: Path, handler) -> tuple[FoodDataService, Database]:
    database = Database(tmp_path / "food.db")
    database.initialize()
    settings = Settings(
        database_path=database.path,
        qdrant_path=tmp_path / "qdrant",
        food_data_enabled=True,
        usda_fdc_api_key="test-key",
        cofid_enabled=False,
    )
    return FoodDataService(settings, database, httpx.MockTransport(handler)), database


def test_arabic_coffee_uses_usda_record_and_cache(tmp_path: Path):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.params["api_key"] == "test-key"
        assert json.loads(request.content)["query"] == "coffee brewed"
        return httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "fdcId": 2710375,
                        "description": "Coffee, brewed",
                        "dataType": "Survey (FNDDS)",
                        "foodNutrients": [
                            {"nutrientId": 1008, "value": 1, "unitName": "KCAL"},
                            {"nutrientId": 1057, "value": 40, "unitName": "MG"},
                        ],
                    }
                ]
            },
        )

    service, database = build_service(tmp_path, handler)
    first = asyncio.run(service.lookup_question("هل القهوة مناسبة؟", mode="food"))
    second = asyncio.run(service.lookup_question("القهوة", mode="food"))
    scaled = asyncio.run(service.lookup_question("200 جم قهوة", mode="food"))

    assert calls == 1
    assert first == second
    assert first["items"][0]["amount_g"] == 100
    assert first["items"][0]["category"] == "beverage"
    assert first["items"][0]["nutrients"]["caffeine_mg"]["value"] == 40
    assert scaled["items"][0]["amount_g"] == 200
    assert scaled["items"][0]["nutrients"]["caffeine_mg"]["value"] == 80
    assert scaled["items"][0]["nutrients"]["calories_kcal"]["value"] == 2
    assert first["items"][0]["source"]["record_id"] == "2710375"
    assert first["items"][0]["source"]["url"].endswith("/2710375/nutrients")
    with database.session() as connection:
        assert connection.execute("SELECT COUNT(*) AS total FROM food_lookup_cache").fetchone()["total"] == 1


def test_mixed_dish_requires_confirmed_ingredients_without_api_call(tmp_path: Path):
    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("Mixed dishes must not be sent to USDA as a single generic food")

    service, _ = build_service(tmp_path, handler)
    result = asyncio.run(service.lookup_question("هل الكشري مناسب؟", mode="food"))

    assert result["items"] == []
    assert "أكّد المكونات والكميات" in result["notices"][0]


def test_failed_source_never_returns_nutrition_numbers(tmp_path: Path):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    service, _ = build_service(tmp_path, handler)
    result = asyncio.run(service.lookup_question("موز", mode="food"))

    assert result["items"] == []
    assert "لم أعرض أي أرقام" in result["notices"][0]


def test_alias_does_not_match_inside_a_different_word(tmp_path: Path):
    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("egg must not match inside eggplant")

    service, _ = build_service(tmp_path, handler)
    result = asyncio.run(service.lookup_question("Is egghead suitable?", mode="food"))

    assert result["items"] == []
    assert "لم أتعرف على طعام محدد" in result["notices"][0]


def test_confirmed_meal_quantity_scales_the_matched_food(tmp_path: Path):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "fdcId": 173944,
                        "description": "Bananas, raw",
                        "dataType": "SR Legacy",
                        "foodNutrients": [
                            {"nutrientId": 1008, "value": 89, "unitName": "KCAL"},
                        ],
                    }
                ]
            },
        )

    service, _ = build_service(tmp_path, handler)
    result = asyncio.run(
        service.lookup_question(
            "حلل الوجبة",
            confirmed_ingredients=["موز"],
            food_quantities=[{"name": "موز", "amount_g": 150}],
            mode="meal",
        )
    )

    assert result["items"][0]["amount_g"] == 150
    assert result["items"][0]["nutrients"]["calories_kcal"]["value"] == 133.5


def test_banana_query_does_not_select_banana_pepper():
    selected = FoodDataService._select_food(
        "banana raw",
        [
            {
                "fdcId": 1,
                "description": "Peppers, banana or Hungarian wax, seeded, raw",
                "dataType": "Foundation",
            },
            {
                "fdcId": 2,
                "description": "Bananas, raw",
                "dataType": "SR Legacy",
            },
        ],
    )

    assert selected["fdcId"] == 2


def test_cofid_provider_reads_exact_official_record(tmp_path: Path):
    dataset_path = tmp_path / "cofid.xlsx"
    workbook = Workbook()
    proximates = workbook.active
    proximates.title = "1.3 Proximates"
    inorganics = workbook.create_sheet("1.4 Inorganics")
    for sheet in (proximates, inorganics):
        sheet.append([])
        sheet.append([])
        sheet.append([])
    proximate_row = [None] * 28
    proximate_row[0] = "11-001"
    proximate_row[1] = "Banana, flesh only, raw"
    proximate_row[2] = "Analytical sample"
    proximate_row[5] = "CoFID test reference"
    proximate_row[9] = 1.1
    proximate_row[10] = 0.3
    proximate_row[11] = 20.3
    proximate_row[12] = 81
    proximate_row[16] = 18.1
    proximate_row[25] = 1.5
    proximate_row[27] = 0.1
    proximates.append(proximate_row)
    mineral_row = [None] * 9
    mineral_row[0] = "11-001"
    mineral_row[7] = 1
    mineral_row[8] = 330
    inorganics.append(mineral_row)
    workbook.save(dataset_path)

    settings = Settings(cofid_enabled=True, cofid_dataset_path=dataset_path)
    provider = CoFIDProvider(
        settings,
        {
            "name": "UK Composition of Foods Integrated Dataset (CoFID) 2021",
            "organization": "Public Health England",
            "website_url": "https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid",
            "license": "Open Government Licence v3.0",
        },
    )
    result = asyncio.run(provider.search({"name_ar": "موز", "query": "banana raw"}))

    assert result["matched_name"] == "Banana, flesh only, raw"
    assert result["source"]["record_id"] == "11-001"
    assert result["nutrients"]["calories_kcal"]["value"] == 81
    assert result["nutrients"]["sodium_mg"]["value"] == 1
    assert result["record_context"]["main_data_reference"] == "CoFID test reference"


def test_cofid_identity_filter_rejects_similarly_named_different_food(tmp_path: Path):
    provider = CoFIDProvider(
        Settings(cofid_enabled=True, cofid_dataset_path=tmp_path / "unused.xlsx"),
        {"name": "UK CoFID 2021"},
    )
    provider.records = [
        {"code": "fish", "name": "Orange roughy, raw", "nutrients": {"protein_g": {"value": 20, "unit": "G"}}},
        {"code": "fruit", "name": "Oranges, flesh only", "nutrients": {"protein_g": {"value": 1, "unit": "G"}}},
    ]

    result = asyncio.run(
        provider.search(
            {
                "name_ar": "برتقال",
                "query": "orange raw",
                "cofid_query": "oranges flesh only",
                "cofid_exclude_tokens": ["roughy"],
            }
        )
    )

    assert result["source"]["record_id"] == "fruit"
    assert result["matched_name"] == "Oranges, flesh only"


def test_two_official_sources_are_compared_without_averaging(tmp_path: Path):
    class StubCoFID:
        def status(self):
            return {"enabled": True, "records_loaded": 1}

        async def search(self, entry):
            return {
                "requested_name": entry["name_ar"],
                "matched_name": "Banana, flesh only, raw",
                "category": "food",
                "basis": "بيانات CoFID لكل 100 جم",
                "nutrients": {
                    "calories_kcal": {"value": 81, "unit": "KCAL"},
                    "protein_g": {"value": 1.1, "unit": "G"},
                },
                "source": {
                    "organization": "Public Health England",
                    "title": "UK CoFID 2021",
                    "record_id": "11-001",
                    "data_type": "CoFID 2021",
                    "url": "https://example.test/cofid",
                    "license": "OGL v3.0",
                },
            }

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "fdcId": 173944,
                        "description": "Bananas, raw",
                        "dataType": "SR Legacy",
                        "foodNutrients": [
                            {"nutrientId": 1008, "value": 89, "unitName": "KCAL"},
                            {"nutrientId": 1003, "value": 1.09, "unitName": "G"},
                        ],
                    }
                ]
            },
        )

    database = Database(tmp_path / "multi-source.db")
    database.initialize()
    settings = Settings(
        database_path=database.path,
        qdrant_path=tmp_path / "qdrant",
        food_data_enabled=True,
        usda_fdc_api_key="test-key",
    )
    service = FoodDataService(
        settings,
        database,
        httpx.MockTransport(handler),
        cofid_provider=StubCoFID(),
    )
    result = asyncio.run(service.lookup_question("200 جم موز", mode="food"))["items"][0]

    assert result["source_count"] == 2
    assert result["source_status"] == "cross_checked_official_sources"
    assert result["nutrients"]["calories_kcal"]["value"] == 178
    assert result["supporting_sources"][0]["nutrients"]["calories_kcal"]["value"] == 162
    comparison = result["source_comparison"]["shared_nutrients"]
    assert comparison[0]["primary_value"] in {178, 2.18}
    assert "لا يتم دمجها أو أخذ متوسطها" in result["source_comparison"]["note"]
