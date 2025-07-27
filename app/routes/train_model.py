
from flask import Blueprint, render_template

train_bp = Blueprint('train', __name__)

@train_bp.route('/')
def dashboard():
    return render_template('train/dashboard.html')
