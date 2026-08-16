from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import current_user
from app.core.security import create_token, hash_password, verify_password
from app.schemas.api import AuthResponse, LoginRequest, RegisterRequest


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request) -> dict:
    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        with request.app.state.db.session() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email,password_hash,name) VALUES (?,?,?)",
                (payload.email.lower(), password_hash, payload.name.strip()),
            )
            user_id = cursor.lastrowid
            connection.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    user = {"id": user_id, "email": payload.email.lower(), "name": payload.name.strip()}
    return {"token": create_token(user_id, request.app.state.settings.secret_key), "user": user}


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request) -> dict:
    with request.app.state.db.session() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (payload.email.lower(),)).fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = {"id": row["id"], "email": row["email"], "name": row["name"]}
    return {"token": create_token(row["id"], request.app.state.settings.secret_key), "user": user}


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


@router.post("/logout")
def logout() -> dict:
    return {"ok": True, "message": "Delete the local bearer token"}

