from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from app.db.database import Database


def medication_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "dose": row["dose"],
        "frequency": row["frequency"],
        "dose_times": json.loads(row["dose_times_json"]),
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "is_permanent": bool(row["is_permanent"]),
        "food_relation": row["food_relation"],
        "notes": row["notes"],
        "active": bool(row["active"]),
    }


def list_medications(db: Database, user_id: int) -> list[dict]:
    with db.session() as connection:
        rows = connection.execute(
            "SELECT * FROM medications WHERE user_id = ? ORDER BY active DESC, created_at DESC", (user_id,)
        ).fetchall()
    return [medication_to_dict(row) for row in rows]


def create_medication(db: Database, user_id: int, payload: dict) -> dict:
    with db.session() as connection:
        cursor = connection.execute(
            """INSERT INTO medications
               (user_id,name,dose,frequency,dose_times_json,start_date,end_date,is_permanent,food_relation,notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                payload["name"],
                payload["dose"],
                payload["frequency"],
                json.dumps(payload["dose_times"]),
                str(payload["start_date"]),
                str(payload["end_date"]) if payload.get("end_date") else None,
                int(payload["is_permanent"]),
                payload.get("food_relation"),
                payload.get("notes", ""),
            ),
        )
        row = connection.execute("SELECT * FROM medications WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return medication_to_dict(row)


def build_schedule(db: Database, user_id: int, target: date | None = None) -> list[dict]:
    target = target or date.today()
    now = datetime.now()
    medications = list_medications(db, user_id)
    schedule: list[dict] = []
    with db.session() as connection:
        for medication in medications:
            if not medication["active"] or target < date.fromisoformat(medication["start_date"]):
                continue
            if medication["end_date"] and target > date.fromisoformat(medication["end_date"]):
                continue
            for dose_time in medication["dose_times"]:
                scheduled = datetime.fromisoformat(f"{target.isoformat()}T{dose_time}:00")
                existing = connection.execute(
                    "SELECT * FROM dose_events WHERE medication_id = ? AND scheduled_at = ?",
                    (medication["id"], scheduled.isoformat()),
                ).fetchone()
                if existing:
                    status = existing["status"]
                else:
                    status = "missed" if scheduled < now - timedelta(hours=2) else "upcoming"
                    connection.execute(
                        "INSERT OR IGNORE INTO dose_events (medication_id,user_id,scheduled_at,status) VALUES (?,?,?,?)",
                        (medication["id"], user_id, scheduled.isoformat(), status),
                    )
                schedule.append(
                    {
                        "medication_id": medication["id"],
                        "name": medication["name"],
                        "dose": medication["dose"],
                        "scheduled_at": scheduled.isoformat(),
                        "status": status,
                        "food_relation": medication["food_relation"],
                    }
                )
    return sorted(schedule, key=lambda item: item["scheduled_at"])


def set_dose_status(db: Database, user_id: int, medication_id: int, scheduled_at: str, status: str) -> dict:
    with db.session() as connection:
        medication = connection.execute(
            "SELECT id FROM medications WHERE id = ? AND user_id = ?", (medication_id, user_id)
        ).fetchone()
        if not medication:
            raise KeyError("Medication not found")
        connection.execute(
            """INSERT INTO dose_events (medication_id,user_id,scheduled_at,status)
               VALUES (?,?,?,?) ON CONFLICT(medication_id,scheduled_at)
               DO UPDATE SET status=excluded.status, recorded_at=CURRENT_TIMESTAMP""",
            (medication_id, user_id, scheduled_at, status),
        )
    return {"medication_id": medication_id, "scheduled_at": scheduled_at, "status": status}


def next_reminders(db: Database, user_id: int) -> list[dict]:
    schedule = build_schedule(db, user_id)
    upcoming = [item for item in schedule if item["status"] == "upcoming"]
    return upcoming[:5]

