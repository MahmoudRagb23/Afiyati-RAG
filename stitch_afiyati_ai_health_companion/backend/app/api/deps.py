from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token


bearer = HTTPBearer(auto_error=False)


def optional_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> dict | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials, request.app.state.settings.secret_key)
    if not payload:
        return None
    with request.app.state.db.session() as connection:
        row = connection.execute(
            """SELECT users.id,users.email,users.name,users.created_at,
                      COALESCE(profiles.onboarding_completed, 0) AS onboarding_completed
               FROM users LEFT JOIN profiles ON profiles.user_id = users.id
               WHERE users.id = ?""",
            (payload["sub"],),
        ).fetchone()
    if not row:
        return None
    user = dict(row)
    user["onboarding_completed"] = bool(user["onboarding_completed"])
    return user


def current_user(user: dict | None = Depends(optional_user)) -> dict:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user
