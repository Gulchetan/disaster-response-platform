from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import AuthError, get_current_user_payload, require_roles
from app.auth.users import Role
from app.db.session import get_db

# Swagger UI "Authorize" sends: Authorization: Bearer <token>
http_bearer = HTTPBearer(auto_error=False)


async def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


def _payload_from_credentials(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if not credentials:
        raise AuthError("Missing or invalid Authorization header")
    return get_current_user_payload(f"Bearer {credentials.credentials}")


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> dict:
    try:
        return _payload_from_credentials(credentials)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


def require_admin(user: dict = Depends(require_auth)) -> dict:
    try:
        require_roles(user, {Role.admin})
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    return user


def require_contributor_or_admin(user: dict = Depends(require_auth)) -> dict:
    try:
        require_roles(user, {Role.admin, Role.contributor})
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    return user
