
from flask import Blueprint, render_template, request, jsonify
import json
import os

trainer_bp = Blueprint('trainer', __name__)

@trainer_bp.route('/')
def training_dashboard():
    return render_template('trainer/dashboard.html')

@trainer_bp.route('/start', methods=['POST'])
def start_training():
    # Placeholder for actual ML model training
    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
    
    try:
        with open(log_path, 'r') as f:
            data_count = sum(1 for line in f)
    except FileNotFoundError:
        return jsonify({"error": "No training data available"})
    
    if data_count < 10:
        return jsonify({"error": "Insufficient data for training (minimum 10 entries required)"})
    
    # Simulate training process
    return jsonify({
        "status": "Training started",
        "data_points": data_count,
        "estimated_time": "5-10 minutes"
    })

@trainer_bp.route('/status')
def training_status():
    # Placeholder for training status
    return jsonify({
        "status": "No active training",
        "last_trained": None,
        "model_accuracy": None
    })
