import sys
import types


class _Request:
    def __init__(self):
        self._json = None

    def get_json(self, *args, **kwargs):
        return self._json


flask_stub = types.SimpleNamespace(
    Blueprint=lambda *a, **k: types.SimpleNamespace(route=lambda *a, **k: (lambda f: f)),
    request=_Request(),
    jsonify=lambda x: x,
    render_template=lambda *a, **k: "",
)

sys.modules['flask'] = flask_stub

from app.routes import scorecard  # noqa: E402


def call_calculate(payload):
    flask_stub.request._json = payload
    resp = scorecard.calculate()
    return resp if isinstance(resp, tuple) else (resp, 200)


def test_finance_valid_submission():
    payload = {
        "owner1_credit_score": 700,
        "intelliscore": 80,
        "daily_average_balance": 10000,
    }
    data, status = call_calculate(payload)
    assert status == 200
    assert data["input"] == payload
    assert "score" in data and "offers" in data


def test_finance_empty_submission():
    data, status = call_calculate({})
    assert status == 400
    assert "error" in data


def test_finance_malformed_submission():
    payload = {
        "owner1_credit_score": "bad",
        "intelliscore": 80,
        "daily_average_balance": 10000,
    }
    data, status = call_calculate(payload)
    assert status == 400
    assert "error" in data


def test_finance_non_dict_payload():
    data, status = call_calculate([1, 2])
    assert status == 400
    assert "error" in data

