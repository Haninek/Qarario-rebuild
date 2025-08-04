import logging

import pytest

from app.utils.scoring import calculate_score


def test_calculate_score_minimal_ruleset():
    rules = {
        "section": {
            "num": {"weight": 10},
            "bool": {"weight": 5},
        }
    }
    input_data = {"num": 7, "bool": "yes"}
    result = calculate_score(input_data, rules)
    assert result == {"total_score": 80.0, "raw_score": 12.0, "max_possible": 15}


def test_calculate_score_invalid_business_start_date(caplog):
    rules = {"section": {"years_in_business": {"weight": 10}}}
    input_data = {"business_start_date": "not-a-date"}
    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError):
            calculate_score(input_data, rules)
    assert "Malformed business start date" in caplog.text

