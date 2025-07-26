
from flask import Blueprint, render_template, request, jsonify
import json
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/rules')
def manage_rules():
    return render_template('admin/rules.html')

@admin_bp.route('/logs')
def view_logs():
    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
    logs = []
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                logs.append(json.loads(line))
    except FileNotFoundError:
        pass
    
    return jsonify(logs[-50:])  # Return last 50 entries
