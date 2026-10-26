from app.auth.jwt import create_access_token, decode_token
from app.auth.users import MOCK_USERS, Role, authenticate


def test_authenticate_valid_user():
    user = authenticate("admin", "admin123")
    assert user is not None
    assert user.role == Role.admin


def test_token_contains_role():
    user = MOCK_USERS["contributor"]
    token = create_access_token(user)
    payload = decode_token(token)
    assert payload["sub"] == "contributor"
    assert payload["role"] == "contributor"
