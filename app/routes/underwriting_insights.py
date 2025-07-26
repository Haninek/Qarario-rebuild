
from flask import Blueprint, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from underwriting_assistant import analyze_logs
import io
import sys

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/')
def insights_dashboard():
    return render_template('insights/dashboard.html')

@insights_bp.route('/show')
def show_insights():
    buffer = io.StringIO()
    sys.stdout = buffer
    analyze_logs()
    sys.stdout = sys.__stdout__
    report = buffer.getvalue()
    return render_template('insights/ml_insights.html', insights=report)

@insights_bp.route('/trends')
def get_trends():
    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
    daily_scores = defaultdict(list)
    risk_distribution = {"Low Risk": 0, "Moderate Risk": 0, "High Risk": 0}
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                timestamp = entry.get("timestamp", "")
                score = entry.get("score", {}).get("total_score", 0)
                
                if timestamp:
                    date = timestamp.split('T')[0]
                    daily_scores[date].append(score)
                
                # Categorize risk
                if score >= 80:
                    risk_distribution["Low Risk"] += 1
                elif score >= 60:
                    risk_distribution["Moderate Risk"] += 1
                else:
                    risk_distribution["High Risk"] += 1
    except FileNotFoundError:
        return jsonify({"error": "No data found"})
    
    # Calculate daily averages
    daily_averages = {date: sum(scores)/len(scores) for date, scores in daily_scores.items()}
    
    return jsonify({
        "daily_averages": daily_averages,
        "risk_distribution": risk_distribution
    })
