from fastapi import APIRouter, HTTPException, status

from app.auth.jwt import create_access_token
from app.auth.users import authenticate
from app.schemas.auth import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(body: TokenRequest) -> TokenResponse:
    user = authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user)
    return TokenResponse(access_token=token, role=user.role.value)
