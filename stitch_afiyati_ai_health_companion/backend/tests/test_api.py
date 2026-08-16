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
    logged_in = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert logged_in.status_code == 200
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
        "conditions": ["type_2_diabetes", "hypertension", "chronic_kidney_disease"],
        "allergies": ["nuts"],
        "dietary_restrictions": ["low sodium"],
        "notes": "Local test",
    }
    updated = client.put("/api/profile", headers=auth_headers, json=payload)
    assert updated.status_code == 200
    loaded = client.get("/api/profile", headers=auth_headers).json()
    assert loaded["conditions"] == payload["conditions"]
    assert loaded["allergies"] == ["nuts"]


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


def test_empty_knowledge_base_refuses_safely(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "هل الموز مناسب ليا؟", "mode": "food"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendation_status"] == "insufficient_evidence"
    assert body["citations"] == []
    assert body["emergency"] is False


def test_emergency_symptoms_work_without_login(client: TestClient):
    response = client.post(
        "/api/symptoms",
        json={"symptoms": "عندي ألم شديد في الصدر وضيق في التنفس", "severity": 9, "context": ""},
    )
    assert response.status_code == 200
    assert response.json()["emergency"] is True
    assert response.json()["safety_classification"] == "POSSIBLE_EMERGENCY"


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
