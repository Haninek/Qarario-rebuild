
from flask import Blueprint, render_template, request, jsonify
import json
import os
from datetime import datetime
import random

ml_bp = Blueprint('ml', __name__)

@ml_bp.route('/')
def ml_dashboard():
    return render_template('ml/dashboard.html')

@ml_bp.route('/train')
def train():
    return render_template('ml/train.html')

@ml_bp.route('/models')
def models():
    return render_template('ml/models.html')

@ml_bp.route('/api/start-training', methods=['POST'])
def start_training():
    """Start a new model training job"""
    try:
        data = request.get_json()
        model_type = data.get('model_type', 'logistic_regression')
        data_source = data.get('data_source', 'historical_loans')
        validation_split = float(data.get('validation_split', 20)) / 100
        
        # Create training job
        job = {
            'id': f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'model_type': model_type,
            'data_source': data_source,
            'validation_split': validation_split,
            'status': 'training',
            'progress': 0,
            'accuracy': 0,
            'loss': 0,
            'started_at': datetime.now().isoformat()
        }
        
        # Save job to file
        jobs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'training_jobs.json')
        os.makedirs(os.path.dirname(jobs_path), exist_ok=True)
        
        try:
            with open(jobs_path, 'r') as f:
                jobs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            jobs = []
        
        jobs.append(job)
        
        with open(jobs_path, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'job_id': job['id'],
            'message': 'Training started successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start training: {str(e)}'
        }), 500

@ml_bp.route('/api/training-status/<job_id>')
def training_status(job_id):
    """Get training job status"""
    try:
        jobs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'training_jobs.json')
        
        try:
            with open(jobs_path, 'r') as f:
                jobs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            jobs = []
        
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job:
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404
        
        # Simulate training progress
        if job['status'] == 'training':
            # Simulate progress
            elapsed_minutes = (datetime.now() - datetime.fromisoformat(job['started_at'])).seconds / 60
            job['progress'] = min(100, elapsed_minutes * 10)  # 10% per minute
            job['accuracy'] = 0.5 + (job['progress'] / 100) * 0.4  # 50% to 90%
            job['loss'] = 2.0 - (job['progress'] / 100) * 1.5  # 2.0 to 0.5
            
            if job['progress'] >= 100:
                job['status'] = 'completed'
                job['completed_at'] = datetime.now().isoformat()
        
        return jsonify({
            'status': 'success',
            'job': job
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get status: {str(e)}'
        }), 500

@ml_bp.route('/api/models')
def api_models():
    """Get list of trained models"""
    models = [
        {
            'id': 'prod-v2.1',
            'name': 'Production Risk Model v2.1',
            'type': 'Random Forest',
            'accuracy': 0.895,
            'status': 'active',
            'created_at': '2024-01-15T10:30:00'
        },
        {
            'id': 'exp-v1.0',
            'name': 'Experimental Neural Net v1.0',
            'type': 'Neural Network',
            'accuracy': 0.782,
            'status': 'testing',
            'created_at': '2024-01-12T15:45:00'
        }
    ]
    
    return jsonify({
        'status': 'success',
        'models': models
    })
