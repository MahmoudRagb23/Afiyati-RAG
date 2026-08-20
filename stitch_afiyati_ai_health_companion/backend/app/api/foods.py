from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user


router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("/sources")
def food_sources(request: Request, user: dict = Depends(current_user)) -> dict:
    return {
        "sources": request.app.state.food_data.source_catalog(),
        "status": request.app.state.food_data.status(),
        "health_rules": request.app.state.health_impacts.catalog(),
        "health_rule_status": request.app.state.health_impacts.status(),
    }


@router.get("/history")
def food_history(request: Request, user: dict = Depends(current_user)) -> list[dict]:
    with request.app.state.db.session() as connection:
        rows = connection.execute(
            """
            SELECT id,question,mode,items_json,created_at
            FROM food_history
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 100
            """,
            (user["id"],),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "question": row["question"],
            "mode": row["mode"],
            "items": json.loads(row["items_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
