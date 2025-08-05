import json

import underwriting_assistant


def test_analyze_logs_numeric_averages(tmp_path, monkeypatch):
    log_file = tmp_path / "underwriting_data.jsonl"
    entries = [
        {"input": {"age": 30}, "score": {"total_score": 1}},
        {"input": {"age": 40}, "score": {"total_score": 2}},
        {"input": {"height": 180}, "score": {"total_score": 3}},
    ]
    with log_file.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    monkeypatch.setattr(underwriting_assistant, "LOG_PATH", log_file)

    report = underwriting_assistant.analyze_logs()

    assert "- age: 35.0" in report
    assert "- height: 180.0" in report
