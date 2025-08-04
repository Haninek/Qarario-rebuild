from app.utils.scoring import calculate_score


def test_numeric_fields_as_strings():
    rules = {
        "section": {
            "utilization": {"weight": 10},
            "inquiries": {"weight": 5},
        }
    }
    input_data = {"utilization": "20", "inquiries": "30"}
    result = calculate_score(input_data, rules)
    assert result == {"total_score": 76.67, "raw_score": 11.5, "max_possible": 15}

