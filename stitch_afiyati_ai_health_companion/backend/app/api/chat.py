from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user
from app.core.conditions import supported_conditions
from app.core.safety import classify_safety, insufficient_evidence_response
from app.schemas.api import ChatRequest


router = APIRouter(prefix="/chat", tags=["ai"])

SOURCE_FOLLOW_UPS = {
    "المصدر",
    "المصادر",
    "ما المصدر",
    "ما هي المصادر",
    "ايه المصدر",
    "ايه المصادر",
    "فين المصدر",
    "هات المصدر",
    "هات المصادر",
    "المصدر ايه",
    "source",
    "sources",
    "references",
    "what is the source",
    "show sources",
}


def _is_source_follow_up(question: str) -> bool:
    cleaned = question.lower().translate(str.maketrans("", "", "؟?!.,،؛:"))
    normalized = " ".join(re.sub(r"[^\w\u0600-\u06ff]+", " ", cleaned).split())
    return normalized in SOURCE_FOLLOW_UPS


def _json_list(value: str | None) -> list[str]:
    try:
        loaded = json.loads(value or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(loaded, list):
        return []
    return [str(item).strip() for item in loaded if str(item).strip()][:20]


def _conversation_context(rows) -> list[dict]:
    context = []
    for row in reversed(rows):
        try:
            response = json.loads(row["response_json"])
        except (json.JSONDecodeError, TypeError):
            continue
        context.append(
            {
                "question": row["question"][:500],
                "answer_summary": str(response.get("summary", ""))[:700],
                "recommendation_status": response.get("recommendation_status"),
            }
        )
    return context


def _source_follow_up_answer(previous: dict | None, conditions: list[str]) -> dict:
    if not previous:
        answer = insufficient_evidence_response(conditions)
        answer["summary"] = "لا توجد إجابة سابقة في المحادثة لعرض مصادرها."
        answer["source_follow_up"] = True
        return answer
    answer = json.loads(json.dumps(previous, ensure_ascii=False))
    health_sources = sum(
        len(assessment.get("sources", []))
        for impact in answer.get("food_health_impacts", [])
        for assessment in impact.get("assessments", [])
    )
    source_count = len(answer.get("citations", [])) + len(answer.get("nutrition_items", [])) + health_sources
    if source_count:
        answer["summary"] = "هذه هي المصادر المباشرة المستخدمة في الإجابة السابقة."
    else:
        answer["summary"] = "الإجابة السابقة لم تتضمن مصدراً يدعم ادعاءً غذائياً أو صحياً."
    answer["conditions_considered"] = []
    answer["suggested_quantity"] = None
    answer["warnings"] = []
    answer["evidence"] = []
    answer["trace_id"] = None
    answer["source_follow_up"] = True
    return answer


@router.post("")
async def chat(payload: ChatRequest, request: Request, user: dict = Depends(current_user)) -> dict:
    with request.app.state.db.session() as connection:
        profile = connection.execute(
            """SELECT age,gender,height_cm,weight_kg,conditions_json,allergies_json,
                      dietary_restrictions_json
               FROM profiles WHERE user_id=?""",
            (user["id"],),
        ).fetchone()
        previous_row = connection.execute(
            """SELECT response_json FROM conversations
               WHERE user_id=? AND COALESCE(intent, '') != 'source_follow_up'
               ORDER BY id DESC LIMIT 1""",
            (user["id"],),
        ).fetchone()
        recent_rows = connection.execute(
            """SELECT question,response_json FROM conversations
               WHERE user_id=? AND COALESCE(intent, '') != 'source_follow_up'
               ORDER BY id DESC LIMIT 3""",
            (user["id"],),
        ).fetchall()
    stored_conditions = _json_list(profile["conditions_json"] if profile else None)
    conditions = supported_conditions(
        payload.conditions if payload.conditions is not None else stored_conditions
    )
    if _is_source_follow_up(payload.question):
        previous = json.loads(previous_row["response_json"]) if previous_row else None
        answer = _source_follow_up_answer(previous, conditions)
        with request.app.state.db.session() as connection:
            connection.execute(
                "INSERT INTO conversations (user_id,question,response_json,intent) VALUES (?,?,?,?)",
                (user["id"], payload.question, json.dumps(answer, ensure_ascii=False), "source_follow_up"),
            )
        return answer

    user_context = {
        "first_name": user["name"].strip().split()[0],
        "age": profile["age"] if profile else None,
        "gender": profile["gender"] if profile else None,
        "height_cm": profile["height_cm"] if profile else None,
        "weight_kg": profile["weight_kg"] if profile else None,
        "registered_conditions": conditions,
        "reported_allergies": _json_list(profile["allergies_json"] if profile else None),
        "dietary_restrictions": _json_list(
            profile["dietary_restrictions_json"] if profile else None
        ),
    }
    conversation_context = _conversation_context(recent_rows)
    question = payload.question
    food_quantities = [item.model_dump() for item in payload.food_quantities or []]
    if food_quantities:
        ingredient_text = ", ".join(
            f"{item['name']} ({item['amount_g']} g)" for item in food_quantities
        )
        question = f"{question}\nConfirmed meal ingredients and weights: {ingredient_text}"
    elif payload.confirmed_ingredients:
        question = f"{question}\nConfirmed meal ingredients: {', '.join(payload.confirmed_ingredients)}"
    food_context = {"items": [], "notices": [], "matched_terms": [], "entries": []}
    safety = classify_safety(question)
    if safety.classification in {"ALLOWED", "CAUTION"} and not safety.emergency:
        food_context = await request.app.state.food_data.lookup_question(
            payload.question,
            payload.confirmed_ingredients,
            food_quantities,
            payload.mode,
        )
    answer, trace = await request.app.state.rag.answer(
        question,
        conditions,
        payload.mode,
        food_context=food_context,
        user_context=user_context,
        conversation_context=conversation_context,
    )
    answer["greeting"] = f"أهلاً يا {user_context['first_name']} 👋"
    answer["profile_context_used"] = bool(
        conditions
        or user_context["reported_allergies"]
        or user_context["dietary_restrictions"]
        or user_context["age"]
    )
    if not answer.get("emergency"):
        answer["nutrition_items"] = food_context["items"]
        answer["food_lookup_notices"] = food_context["notices"]
        answer["food_health_impacts"] = request.app.state.health_impacts.assess(
            food_context, conditions
        )
        if answer["food_health_impacts"]:
            answer["conditions_considered"] = []
    trace["food_lookup"] = food_context
    with request.app.state.db.session() as connection:
        conversation = connection.execute(
            "INSERT INTO conversations (user_id,question,response_json,intent) VALUES (?,?,?,?)",
            (user["id"], payload.question, json.dumps(answer, ensure_ascii=False), trace.get("analysis", {}).get("intent")),
        )
        if food_context["items"]:
            connection.execute(
                "INSERT INTO food_history (user_id,conversation_id,question,mode,items_json) VALUES (?,?,?,?,?)",
                (
                    user["id"],
                    conversation.lastrowid,
                    payload.question,
                    payload.mode,
                    json.dumps(food_context["items"], ensure_ascii=False),
                ),
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
