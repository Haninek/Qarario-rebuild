from flask import Blueprint, request, jsonify, render_template
import json
import os
from datetime import datetime
from app.utils.scoring import calculate_score, classify_risk
from app.utils.offers import generate_loan_offers

scorecard_bp = Blueprint('scorecard', __name__)

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'rules',
                          'finance.json')
with open(RULES_PATH) as f:
    RULES = json.load(f)


@scorecard_bp.route('/')
def form():
    return render_template('form.html')

@scorecard_bp.route('')
def form_no_slash():
    return render_template('form.html')


@scorecard_bp.route('/finance-rules')
def rules():
    return jsonify(RULES)


@scorecard_bp.route('/questionnaire')
def questionnaire():
    return render_template('questionnaire.html', rules=RULES)


@scorecard_bp.route('/finance', methods=['POST'])
def calculate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    required_numeric = [
        "owner1_credit_score",
        "intelliscore",
        "daily_average_balance",
    ]
    missing = [field for field in required_numeric if field not in data]
    if missing:
        msg = ", ".join(missing)
        return jsonify({"error": f"Missing required fields: {msg}"}), 400

    non_numeric = []
    for field in required_numeric:
        try:
            float(data[field])
        except (TypeError, ValueError):
            non_numeric.append(field)
    if non_numeric:
        msg = ", ".join(non_numeric)
        return jsonify({"error": f"Fields must be numeric: {msg}"}), 400

    result = calculate_score(data, RULES)
    tier = classify_risk(result['total_score'])
    offers = generate_loan_offers(result['total_score'], data)

    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": data,
        "score": result,
        "offers": offers,
        "tier": tier,
    }

    # Use buffered logging from main.py
    from main import add_to_log_buffer
    add_to_log_buffer(log)

    return jsonify({"score": result, "offers": offers, "tier": tier, "input": data})
