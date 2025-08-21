
from flask import Blueprint, render_template

train_bp = Blueprint('train', __name__)

@train_bp.route('/')
def dashboard():
    return render_template('train/dashboard.html')

@train_bp.route('/start')
def start_training():
    return render_template('train/start.html')

@train_bp.route('/models')
def models():
    return render_template('train/models.html')
