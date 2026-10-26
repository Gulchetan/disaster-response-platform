from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.auth.users import MockUser, Role
from app.config import settings


def create_access_token(user: MockUser) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": user.username,
        "role": user.role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


class AuthError(Exception):
    pass


def get_current_user_payload(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_token(token)
    except JWTError as e:
        raise AuthError("Invalid or expired token") from e


def require_roles(payload: dict[str, Any], allowed: set[Role]) -> None:
    role = payload.get("role")
    if role not in {r.value for r in allowed}:
        raise AuthError("Insufficient permissions")
