from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["rag"]["indexed_chunks"] == 0


def test_benchmark_report_endpoint_is_always_machine_readable(client: TestClient):
    response = client.get("/api/rag/benchmark")
    assert response.status_code == 200
    assert "evaluation_status" in response.json()


def test_registration_login_and_password_not_plaintext(client: TestClient):
    payload = {"name": "Ahmed", "email": "ahmed@example.com", "password": "strong-password"}
    registered = client.post("/api/auth/register", json=payload)
    assert registered.status_code == 201
    assert registered.json()["user"]["onboarding_completed"] is False
    logged_in = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert logged_in.status_code == 200
    assert logged_in.json()["user"]["onboarding_completed"] is False
    with client.app.state.db.session() as connection:
        row = connection.execute("SELECT password_hash FROM users WHERE email=?", (payload["email"],)).fetchone()
    assert payload["password"] not in row["password_hash"]
    assert row["password_hash"].startswith("scrypt$")


def test_profile_persists_multiple_conditions(client: TestClient, auth_headers: dict):
    payload = {
        "name": "Test User",
        "age": 46,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 82,
        "conditions": ["type_2_diabetes", "hypertension"],
        "allergies": ["nuts"],
        "dietary_restrictions": ["low sodium"],
        "notes": "Local test",
    }
    updated = client.put("/api/profile", headers=auth_headers, json=payload)
    assert updated.status_code == 200
    loaded = client.get("/api/profile", headers=auth_headers).json()
    assert loaded["conditions"] == payload["conditions"]
    assert loaded["allergies"] == ["nuts"]
    assert loaded["onboarding_completed"] is True


def test_profile_rejects_unsupported_conditions(client: TestClient, auth_headers: dict):
    payload = {
        "name": "Test User",
        "conditions": ["hypertension", "unsupported_condition"],
        "allergies": [],
    }
    response = client.put("/api/profile", headers=auth_headers, json=payload)
    assert response.status_code == 422
    assert client.get("/api/profile", headers=auth_headers).json()["conditions"] == []


def test_legacy_profile_conditions_are_hidden(client: TestClient, auth_headers: dict):
    with client.app.state.db.session() as connection:
        connection.execute(
            "UPDATE profiles SET conditions_json=?",
            ('["hypertension","unsupported_condition"]',),
        )
    loaded = client.get("/api/profile", headers=auth_headers).json()
    assert loaded["conditions"] == ["hypertension"]


def test_medication_schedule_status_and_temporary_end(client: TestClient, auth_headers: dict):
    today = date.today()
    permanent = {
        "name": "Metformin",
        "dose": "500mg",
        "frequency": 1,
        "dose_times": ["23:59"],
        "start_date": str(today),
        "end_date": None,
        "is_permanent": True,
        "food_relation": "after_food",
        "notes": "prescribed",
    }
    created = client.post("/api/medications", headers=auth_headers, json=permanent)
    assert created.status_code == 201
    schedule = client.get("/api/medications/schedule/today", headers=auth_headers).json()
    assert len(schedule) == 1
    event = schedule[0]
    marked = client.post(
        f"/api/medications/{created.json()['id']}/dose",
        headers=auth_headers,
        json={"scheduled_at": event["scheduled_at"], "status": "taken"},
    )
    assert marked.status_code == 200
    assert client.get("/api/medications/schedule/today", headers=auth_headers).json()[0]["status"] == "taken"

    ended = {
        **permanent,
        "name": "Temporary course",
        "start_date": str(today - timedelta(days=3)),
        "end_date": str(today - timedelta(days=1)),
        "is_permanent": False,
    }
    assert client.post("/api/medications", headers=auth_headers, json=ended).status_code == 201
    names = [item["name"] for item in client.get("/api/medications/schedule/today", headers=auth_headers).json()]
    assert "Temporary course" not in names


def test_empty_knowledge_base_returns_a_sourced_supported_condition_fallback(
    client: TestClient, auth_headers: dict
):
    response = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "هل تقليل الملح مفيد للضغط؟", "mode": "chat"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendation_status"] == "caution"
    assert body["citations"][0]["organization"] == "National Institute for Health and Care Excellence (NICE)"
    assert "تقليل الملح" in body["summary"]
    assert body["emergency"] is False


def test_unsupported_condition_gets_a_polite_in_scope_boundary(
    client: TestClient, auth_headers: dict
):
    response = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "هل القهوة مناسبة مع الربو؟", "mode": "food"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_classification"] == "UNSUPPORTED_CONDITION"
    assert "لا تتوفر لدى عافيتي معلومات موثقة عن الربو" in body["summary"]
    assert body["nutrition_items"] == []
    assert body["food_health_impacts"] == []


def test_chat_receives_safe_profile_and_recent_conversation_context(client: TestClient, auth_headers: dict):
    profile = {
        "name": "Test User",
        "age": 46,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 82,
        "conditions": ["hypertension"],
        "allergies": ["فول سوداني"],
        "dietary_restrictions": ["قليل الصوديوم"],
        "notes": "must never be sent to the model",
    }
    assert client.put("/api/profile", headers=auth_headers, json=profile).status_code == 200
    captured = []

    class StubRag:
        class Vectors:
            @staticmethod
            def close():
                return None

        vectors = Vectors()

        async def answer(
            self,
            question,
            conditions,
            mode="chat",
            food_context=None,
            user_context=None,
            conversation_context=None,
        ):
            captured.append(
                {
                    "question": question,
                    "conditions": conditions,
                    "user_context": user_context,
                    "conversation_context": conversation_context,
                }
            )
            return (
                {
                    "summary": "إجابة عربية آمنة",
                    "recommendation_status": "insufficient_evidence",
                    "conditions_considered": [],
                    "suggested_quantity": None,
                    "warnings": [],
                    "evidence_strength": "insufficient",
                    "citations": [],
                    "needs_professional_attention": False,
                    "emergency": False,
                    "safety_classification": "ALLOWED",
                    "trace_id": None,
                    "evidence": [],
                },
                {"analysis": {"intent": "food"}},
            )

    client.app.state.rag = StubRag()
    first = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "هل الموز مناسب؟", "mode": "chat"},
    )
    second = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "وماذا عن التفاح؟", "mode": "chat"},
    )

    assert first.json()["greeting"] == "أهلاً يا Test 👋"
    assert first.json()["profile_context_used"] is True
    assert captured[0]["user_context"]["reported_allergies"] == ["فول سوداني"]
    assert "notes" not in captured[0]["user_context"]
    assert captured[0]["conversation_context"] == []
    assert captured[1]["conversation_context"][0]["question"] == "هل الموز مناسب؟"


def test_food_source_catalog_is_exposed_to_signed_in_user(client: TestClient, auth_headers: dict):
    response = client.get("/api/foods/sources", headers=auth_headers)

    assert response.status_code == 200
    source_ids = {item["id"] for item in response.json()["sources"]}
    assert {"usda_fdc", "uk_cofid_2021", "fao_infoods"} <= source_ids
    assert response.json()["health_rules"]["medical_sources"]
    assert response.json()["health_rules"]["activities"]
    assert "api_key" not in str(response.json()).lower()


def test_food_health_impact_uses_stored_condition_and_preserves_medical_source(
    client: TestClient, auth_headers: dict
):
    assert client.put(
        "/api/profile",
        headers=auth_headers,
        json={"name": "Test User", "conditions": ["hypertension"], "allergies": []},
    ).status_code == 200

    class StubFoodData:
        async def lookup_question(self, question, confirmed_ingredients, food_quantities, mode):
            return {
                "items": [],
                "notices": [],
                "matched_terms": ["قهوة سوداء"],
                "entries": [
                    {
                        "name_ar": "قهوة سوداء",
                        "category": "beverage",
                        "requires_ingredients": False,
                        "amount_g": 100,
                        "amount_provided": False,
                    }
                ],
            }

    client.app.state.food_data = StubFoodData()
    answer = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "هل القهوة مناسبة؟", "mode": "food"},
    ).json()

    impact = answer["food_health_impacts"][0]["assessments"][0]
    assert impact["condition"] == "hypertension"
    assert impact["action"] == "ask_quantity"
    assert impact["sources"][0]["organization"] == "National Institute for Health and Care Excellence (NICE)"


def test_food_source_is_preserved_and_returned_on_source_follow_up(client: TestClient, auth_headers: dict):
    item = {
        "requested_name": "قهوة سوداء",
        "matched_name": "Coffee, brewed",
        "category": "beverage",
        "amount_g": 200,
        "basis": "للكمية المحددة: 200 جم (بيانات USDA لكل 100 جم)",
        "nutrients": {"caffeine_mg": {"value": 80, "unit": "MG"}},
        "source": {
            "organization": "U.S. Department of Agriculture, Agricultural Research Service",
            "title": "USDA FoodData Central",
            "record_id": "2710375",
            "data_type": "Survey (FNDDS)",
            "url": "https://fdc.nal.usda.gov/fdc-app.html#/food-details/2710375/nutrients",
            "license": "CC0 1.0 Universal",
        },
    }

    class StubFoodData:
        async def lookup_question(self, question, confirmed_ingredients, food_quantities, mode):
            assert food_quantities == [{"name": "قهوة", "amount_g": 200.0}]
            return {"items": [item], "notices": [], "matched_terms": ["قهوة سوداء"]}

    client.app.state.food_data = StubFoodData()
    first = client.post(
        "/api/chat",
        headers=auth_headers,
        json={
            "question": "ما القيم الغذائية للقهوة؟",
            "food_quantities": [{"name": "قهوة", "amount_g": 200}],
            "mode": "food",
        },
    )
    assert first.status_code == 200
    assert first.json()["nutrition_items"][0]["amount_g"] == 200
    assert first.json()["nutrition_items"][0]["source"]["record_id"] == "2710375"
    history = client.get("/api/foods/history", headers=auth_headers)
    assert history.status_code == 200
    assert history.json()[0]["items"][0]["amount_g"] == 200

    follow_up = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "ما المصدر؟", "mode": "chat"},
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["source_follow_up"] is True
    assert follow_up.json()["nutrition_items"][0]["source"]["url"] == item["source"]["url"]
    assert len(client.get("/api/foods/history", headers=auth_headers).json()) == 1


def test_food_quantity_validation_rejects_invalid_weights(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/chat",
        headers=auth_headers,
        json={
            "question": "حلل الموز",
            "food_quantities": [{"name": "موز", "amount_g": 0}],
            "mode": "food",
        },
    )
    assert response.status_code == 422


def test_existing_food_conversations_are_backfilled_once(client: TestClient, auth_headers: dict):
    with client.app.state.db.session() as connection:
        user_id = connection.execute(
            "SELECT id FROM users WHERE email=?", ("test@example.com",)
        ).fetchone()["id"]
        connection.execute(
            "INSERT INTO conversations (user_id,question,response_json,intent) VALUES (?,?,?,?)",
            (
                user_id,
                "150 جم موز",
                '{"nutrition_items":[{"requested_name":"موز","matched_name":"Bananas, raw","amount_g":150,"nutrients":{},"source":{"record_id":"173944","url":"https://example.test/173944","title":"USDA FoodData Central"}}]}',
                "food",
            ),
        )

    client.app.state.db.initialize()
    client.app.state.db.initialize()
    history = client.get("/api/foods/history", headers=auth_headers).json()

    assert len(history) == 1
    assert history[0]["items"][0]["amount_g"] == 150


def test_emergency_symptoms_work_without_login(client: TestClient):
    response = client.post(
        "/api/symptoms",
        json={"symptoms": "عندي ألم شديد في الصدر وضيق في التنفس", "severity": 9, "context": ""},
    )
    assert response.status_code == 200
    assert response.json()["emergency"] is True
    assert response.json()["safety_classification"] == "POSSIBLE_EMERGENCY"


def test_chat_sends_colloquial_choking_to_emergency_before_generation(
    client: TestClient, auth_headers: dict
):
    response = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "حاسس بالاختناق ومش قادر أخد نفسي", "mode": "chat"},
    )

    assert response.status_code == 200
    assert response.json()["emergency"] is True
    assert response.json()["safety_classification"] == "POSSIBLE_EMERGENCY"


def test_signed_in_user_can_review_recent_symptom_check_ins(client: TestClient, auth_headers: dict):
    assert client.post(
        "/api/symptoms",
        headers=auth_headers,
        json={"symptoms": "دوخة خفيفة", "severity": 3, "context": "منذ ساعة"},
    ).status_code == 200

    history = client.get("/api/symptoms/history", headers=auth_headers)

    assert history.status_code == 200
    assert history.json()[0]["symptoms"] == "دوخة خفيفة منذ ساعة"
    assert history.json()[0]["severity"] == 3


def test_meal_detection_is_non_medical_and_requires_confirmation(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/meals/detect",
        headers=auth_headers,
        files={"file": ("meal.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requires_confirmation"] is True
    assert body["mode"] == "demo_local_fallback"
