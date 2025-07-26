
from flask import Blueprint, render_template, request, jsonify
import json
import os
from collections import defaultdict

ml_bp = Blueprint('ml_training', __name__)

@ml_bp.route('/')
def ml_dashboard():
    return render_template('ml/dashboard.html')

@ml_bp.route('/analyze')
def analyze_data():
    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
    scores = []
    field_frequency = defaultdict(int)
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                input_data = entry.get("input", {})
                score_data = entry.get("score", {}).get("total_score", 0)
                scores.append(score_data)
                
                for field, value in input_data.items():
                    if isinstance(value, str) and value.strip():
                        field_frequency[field] += 1
    except FileNotFoundError:
        return jsonify({"error": "No training data found"})
    
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    top_fields = sorted(field_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return jsonify({
        "average_score": avg_score,
        "total_entries": len(scores),
        "top_fields": top_fields
    })
