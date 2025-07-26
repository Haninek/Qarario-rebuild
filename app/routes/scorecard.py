from flask import Blueprint, render_template, request, jsonify
import json
import os
from app.utils.scoring import calculate_score
from app.utils.offers import generate_loan_offers
from datetime import datetime

scorecard_bp = Blueprint('scorecard', __name__)

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'rules', 'finance.json')
with open(RULES_PATH) as f:
    RULES = json.load(f)

@scorecard_bp.route('/')
def index():
    return render_template('form.html')

@scorecard_bp.route('/finance-rules')
def finance_rules():
    return jsonify(RULES)

@scorecard_bp.route('/finance', methods=['POST'])
def finance_score():
    data = request.get_json()
    score_result = calculate_score(data, RULES)
    offers = generate_loan_offers(score_result['total_score'])

    # Log inputs for ML learning
    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
    with open(log_path, 'a') as log_file:
        log_file.write(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "input": data,
            "score": score_result
        }) + '\n')

    return jsonify({"score": score_result, "input": data, "offers": offers})
