from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.api.deps import current_user, optional_user
from app.core.safety import classify_safety, emergency_response
from app.schemas.api import SymptomRequest


router = APIRouter(tags=["health-tools"])


@router.post("/meals/detect")
async def detect_meal(
    file: UploadFile = File(...), user: dict = Depends(current_user)
) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image file")
    return {
        "mode": "demo_local_fallback",
        "requires_confirmation": True,
        "ingredients": ["دجاج مشوي", "أرز مطبوخ", "سلطة خضراء"],
        "notice": "لم يتم العثور على نموذج رؤية محلي مهيأ؛ عدّل المكونات ثم أكدها قبل التحليل الطبي.",
    }


@router.post("/symptoms")
async def symptoms(
    payload: SymptomRequest, request: Request, user: dict | None = Depends(optional_user)
) -> dict:
    text = f"{payload.symptoms} {payload.context}".strip()
    safety = classify_safety(text, payload.severity)
    if safety.emergency:
        answer = emergency_response()
        classification = "possible_emergency"
    elif payload.severity >= 6:
        answer = {
            "classification": "professional_evaluation_recommended",
            "message": "ينصح بالتواصل مع مختص صحي لتقييم الأعراض، خصوصاً إذا كانت تتفاقم.",
            "emergency": False,
        }
        classification = "professional_evaluation_recommended"
    else:
        answer = {
            "classification": "monitoring",
            "message": "راقب الأعراض وسجل أي تغير. اطلب تقييماً مهنياً إذا استمرت أو ساءت.",
            "emergency": False,
        }
        classification = "monitoring"
    with request.app.state.db.session() as connection:
        connection.execute(
            "INSERT INTO symptoms (user_id,symptoms,started_at,severity,classification) VALUES (?,?,?,?,?)",
            (user["id"] if user else None, text, payload.started_at, payload.severity, classification),
        )
    return answer


@router.get("/rag/status")
def rag_status(request: Request) -> dict:
    return request.app.state.rag.status()


@router.get("/rag/benchmark")
def rag_benchmark(request: Request) -> dict:
    report_path = request.app.state.settings.root_dir / "evaluation" / "reports" / "latest.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return {
            "evaluation_status": report.get("evaluation_status", "LEGACY REPORT — RERUN BENCHMARK"),
            **report,
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "evaluation_status": "NOT EVALUATED — RUN THE BENCHMARK",
            "official_metrics_status": "DATA REQUIRED",
            "retrieval": {"status": "NOT EVALUATED — RUN THE BENCHMARK"},
            "grounding": {"status": "NOT EVALUATED — RUN WITH --full"},
        }


@router.get("/rag/traces/{trace_id}")
def rag_trace(trace_id: str, request: Request, user: dict = Depends(current_user)) -> dict:
    trace = request.app.state.rag.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Technical trace not found")
    return trace


@router.get("/sources")
def sources(request: Request, user: dict = Depends(current_user)) -> list[dict]:
    unique: dict[str, dict] = {}
    for chunk in request.app.state.rag.bm25.chunks:
        meta = chunk["metadata"]
        key = meta.get("guideline_id") or meta.get("source_filename")
        unique[key] = {
            "guideline_id": meta.get("guideline_id"),
            "title": meta.get("guideline_title"),
            "organization": meta.get("organization"),
            "condition": meta.get("condition"),
            "publication_year": meta.get("publication_year"),
            "version": meta.get("guideline_version"),
            "source_url": meta.get("source_url"),
        }
    return list(unique.values())
