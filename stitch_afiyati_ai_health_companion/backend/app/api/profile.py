from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user
from app.schemas.api import ProfileUpdate


router = APIRouter(prefix="/profile", tags=["profile"])


def _profile_dict(user: dict, row) -> dict:
    return {
        "name": user["name"],
        "email": user["email"],
        "age": row["age"],
        "gender": row["gender"],
        "height_cm": row["height_cm"],
        "weight_kg": row["weight_kg"],
        "conditions": json.loads(row["conditions_json"]),
        "allergies": json.loads(row["allergies_json"]),
        "dietary_restrictions": json.loads(row["dietary_restrictions_json"]),
        "notes": row["notes"],
    }


@router.get("")
def get_profile(request: Request, user: dict = Depends(current_user)) -> dict:
    with request.app.state.db.session() as connection:
        row = connection.execute("SELECT * FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
    return _profile_dict(user, row)


@router.put("")
def update_profile(payload: ProfileUpdate, request: Request, user: dict = Depends(current_user)) -> dict:
    with request.app.state.db.session() as connection:
        connection.execute("UPDATE users SET name = ? WHERE id = ?", (payload.name.strip(), user["id"]))
        connection.execute(
            """UPDATE profiles SET age=?,gender=?,height_cm=?,weight_kg=?,conditions_json=?,
               allergies_json=?,dietary_restrictions_json=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=?""",
            (
                payload.age,
                payload.gender,
                payload.height_cm,
                payload.weight_kg,
                json.dumps(payload.conditions),
                json.dumps(payload.allergies, ensure_ascii=False),
                json.dumps(payload.dietary_restrictions, ensure_ascii=False),
                payload.notes,
                user["id"],
            ),
        )
        row = connection.execute("SELECT * FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
    return _profile_dict({**user, "name": payload.name.strip()}, row)

