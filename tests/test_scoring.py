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

