from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    admin = "admin"
    contributor = "contributor"


@dataclass(frozen=True)
class MockUser:
    username: str
    password: str
    role: Role


MOCK_USERS: dict[str, MockUser] = {
    "admin": MockUser("admin", "admin123", Role.admin),
    "contributor": MockUser("contributor", "contrib123", Role.contributor),
}


def authenticate(username: str, password: str) -> MockUser | None:
    user = MOCK_USERS.get(username)
    if user and user.password == password:
        return user
    return None
