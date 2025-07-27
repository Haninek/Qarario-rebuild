
from flask import Blueprint, render_template

ml_bp = Blueprint('ml_training', __name__)

@ml_bp.route('/')
def dashboard():
    return render_template('ml/dashboard.html')
