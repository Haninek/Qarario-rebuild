import pytest

from app.utils.scoring import classify_risk


@pytest.mark.parametrize("score,expected", [
    (85, "low"),
    (70, "moderate"),
    (55, "high"),
    (40, "super_high"),
])
def test_classify_risk(score, expected):
    assert classify_risk(score) == expected
