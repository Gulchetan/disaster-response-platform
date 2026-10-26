import pytest
from pydantic import ValidationError

from app.schemas.disaster import DisasterCreate


def test_disaster_create_rejects_short_title():
    with pytest.raises(ValidationError) as exc:
        DisasterCreate(title="ab", description="Valid description here.", tags=[])
    assert "title" in str(exc.value)


def test_disaster_create_normalizes_tags():
    body = DisasterCreate(title="Valid title", description="Enough characters in description.", tags=[" Flood ", ""])
    assert body.tags == ["flood"]
