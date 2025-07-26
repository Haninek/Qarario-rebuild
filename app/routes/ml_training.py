from flask import Blueprint, render_template

ml_bp = Blueprint('ml_training', __name__)

@ml_bp.route('/')
def dashboard():
    return render_template('ml/dashboard.html')

@ml_bp.route('/train')
def train():
    return render_template('ml/dashboard.html')

@ml_bp.route('/models')
def models():
    return render_template('ml/dashboard.html')