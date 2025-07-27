from flask import Blueprint, render_template
from underwriting_assistant import analyze_logs

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/')
def insights():
    report = analyze_logs()
    return render_template('insights.html', insights=report)
