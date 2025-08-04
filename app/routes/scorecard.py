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

# Support accessing the scoring form without a trailing slash.  Flask's
# default behaviour distinguishes between `/score` and `/score/` when using
# blueprints with a url_prefix.  Adding this route makes both variants
# resolve to the same view.
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
    data = request.get_json()
    result = calculate_score(data, RULES)
    tier = classify_risk(result['total_score'])
    offers = generate_loan_offers(result['total_score'])

    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": data,
        "score": result,
        "offers": offers,
        "tier": tier,
    }

    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs',
                            'underwriting_data.jsonl')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(json.dumps(log) + '\n')

    return jsonify({"score": result, "offers": offers, "tier": tier, "input": data})
