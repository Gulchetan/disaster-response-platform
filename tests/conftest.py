import os

import pytest

# Force deterministic mocks for CI/local without Groq key
os.environ.setdefault("USE_MOCK_LLM", "true")
os.environ.setdefault("USE_MOCK_GEOCODING", "true")
os.environ.setdefault("JWT_SECRET", "test-secret")


@pytest.fixture
def anyio_backend():
    return "asyncio"
