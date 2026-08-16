from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user
from app.schemas.api import ChatRequest


router = APIRouter(prefix="/chat", tags=["ai"])


@router.post("")
async def chat(payload: ChatRequest, request: Request, user: dict = Depends(current_user)) -> dict:
    with request.app.state.db.session() as connection:
        profile = connection.execute("SELECT conditions_json FROM profiles WHERE user_id=?", (user["id"],)).fetchone()
    conditions = payload.conditions if payload.conditions is not None else json.loads(profile["conditions_json"])
    question = payload.question
    if payload.confirmed_ingredients:
        question = f"{question}\nConfirmed meal ingredients: {', '.join(payload.confirmed_ingredients)}"
    answer, trace = await request.app.state.rag.answer(question, conditions, payload.mode)
    with request.app.state.db.session() as connection:
        connection.execute(
            "INSERT INTO conversations (user_id,question,response_json,intent) VALUES (?,?,?,?)",
            (user["id"], payload.question, json.dumps(answer, ensure_ascii=False), trace.get("analysis", {}).get("intent")),
        )
    return answer


@router.get("/history")
def history(request: Request, user: dict = Depends(current_user)) -> list[dict]:
    with request.app.state.db.session() as connection:
        rows = connection.execute(
            "SELECT id,question,response_json,intent,created_at FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT 50",
            (user["id"],),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "question": row["question"],
            "response": json.loads(row["response_json"]),
            "intent": row["intent"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]

