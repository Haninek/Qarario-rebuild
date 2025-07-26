
from flask import Blueprint, render_template, jsonify
import json
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/rules')
def rules():
    rules_path = os.path.join(os.path.dirname(__file__), '..', 'rules', 'finance.json')
    with open(rules_path) as f:
        rules = json.load(f)
    return render_template('admin/rules.html', rules=rules)

@admin_bp.route('/logs')
def logs():
    """Return recent underwriting logs as JSON"""
    try:
        log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
        logs = []
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue  # Skip malformed lines
        
        # Return the most recent 50 logs
        return jsonify(logs[-50:])
    except Exception as e:
        return jsonify([]), 500

@admin_bp.route('/ml-insights')
def ml_insights():
    from underwriting_assistant import analyze_logs
    insights = analyze_logs()
    return render_template('admin/ml_insights.html', insights=insights)
