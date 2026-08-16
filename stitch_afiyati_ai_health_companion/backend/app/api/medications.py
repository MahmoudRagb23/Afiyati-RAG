from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import current_user
from app.schemas.api import DoseStatusRequest, MedicationCreate
from app.services.medication_service import (
    build_schedule,
    create_medication,
    list_medications,
    next_reminders,
    set_dose_status,
)


router = APIRouter(prefix="/medications", tags=["medications"])


@router.get("")
def list_all(request: Request, user: dict = Depends(current_user)) -> list[dict]:
    return list_medications(request.app.state.db, user["id"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: MedicationCreate, request: Request, user: dict = Depends(current_user)) -> dict:
    return create_medication(request.app.state.db, user["id"], payload.model_dump())


@router.put("/{medication_id}")
def update(
    medication_id: int, payload: MedicationCreate, request: Request, user: dict = Depends(current_user)
) -> dict:
    values = payload.model_dump()
    with request.app.state.db.session() as connection:
        cursor = connection.execute(
            """UPDATE medications SET name=?,dose=?,frequency=?,dose_times_json=?,start_date=?,end_date=?,
               is_permanent=?,food_relation=?,notes=? WHERE id=? AND user_id=?""",
            (
                values["name"],
                values["dose"],
                values["frequency"],
                json.dumps(values["dose_times"]),
                str(values["start_date"]),
                str(values["end_date"]) if values.get("end_date") else None,
                int(values["is_permanent"]),
                values["food_relation"],
                values["notes"],
                medication_id,
                user["id"],
            ),
        )
        if not cursor.rowcount:
            raise HTTPException(status_code=404, detail="Medication not found")
    return next(item for item in list_medications(request.app.state.db, user["id"]) if item["id"] == medication_id)


@router.delete("/{medication_id}")
def stop(medication_id: int, request: Request, user: dict = Depends(current_user)) -> dict:
    with request.app.state.db.session() as connection:
        cursor = connection.execute(
            "UPDATE medications SET active=0 WHERE id=? AND user_id=?", (medication_id, user["id"])
        )
        if not cursor.rowcount:
            raise HTTPException(status_code=404, detail="Medication not found")
    return {"ok": True, "medication_id": medication_id}


@router.get("/schedule/today")
def schedule(
    request: Request,
    on: date | None = Query(default=None),
    user: dict = Depends(current_user),
) -> list[dict]:
    return build_schedule(request.app.state.db, user["id"], on)


@router.post("/{medication_id}/dose")
def record_dose(
    medication_id: int,
    payload: DoseStatusRequest,
    request: Request,
    user: dict = Depends(current_user),
) -> dict:
    try:
        return set_dose_status(
            request.app.state.db, user["id"], medication_id, payload.scheduled_at, payload.status
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reminders/upcoming")
def reminders(request: Request, user: dict = Depends(current_user)) -> list[dict]:
    return next_reminders(request.app.state.db, user["id"])
