from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


Condition = Literal["hypertension", "type_2_diabetes"]


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    age: int | None = Field(default=None, ge=13, le=120)
    gender: str | None = None
    height_cm: float | None = Field(default=None, ge=80, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=400)
    conditions: list[Condition] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class MedicationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    dose: str = Field(min_length=1, max_length=80)
    frequency: int = Field(default=1, ge=1, le=12)
    dose_times: list[str] = Field(min_length=1, max_length=12)
    start_date: date
    end_date: date | None = None
    is_permanent: bool = True
    food_relation: Literal["before_food", "after_food", "with_food", "any"] = "any"
    notes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def validate_schedule(self) -> "MedicationCreate":
        if self.frequency != len(self.dose_times):
            raise ValueError("frequency must match the number of dose times")
        for value in self.dose_times:
            hour, minute = value.split(":")
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError("dose times must use HH:MM")
        if not self.is_permanent and not self.end_date:
            raise ValueError("temporary medication requires an end date")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end date cannot be before start date")
        return self


class DoseStatusRequest(BaseModel):
    scheduled_at: str
    status: Literal["taken", "missed", "skipped"]


class FoodQuantity(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount_g: float = Field(ge=1, le=5000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    conditions: list[Condition] | None = None
    confirmed_ingredients: list[str] | None = None
    food_quantities: list[FoodQuantity] | None = Field(default=None, max_length=20)
    mode: Literal["chat", "food", "meal", "habit", "symptom"] = "chat"


class Citation(BaseModel):
    document: str
    organization: str
    section: str | None = None
    page: int | None = None
    chunk_id: str
    source_url: str | None = None


class ConditionAssessment(BaseModel):
    condition: str
    assessment: str


class SuggestedQuantity(BaseModel):
    value: str
    basis: str
    certainty: str


class AfiyatiAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str
    recommendation_status: Literal[
        "suitable", "caution", "not_recommended", "insufficient_evidence"
    ]
    conditions_considered: list[ConditionAssessment] = []
    suggested_quantity: SuggestedQuantity | None = None
    warnings: list[str] = []
    evidence_strength: Literal["strong", "moderate", "limited", "insufficient"]
    citations: list[Citation] = []
    needs_professional_attention: bool = False
    emergency: bool = False
    safety_classification: str = "ALLOWED"
    trace_id: str | None = None
    evidence: list[dict] = []


class SymptomRequest(BaseModel):
    symptoms: str = Field(min_length=2, max_length=2000)
    started_at: str | None = None
    severity: int = Field(ge=1, le=10)
    context: str = Field(default="", max_length=1000)
