
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

@ml_bp.route('/feedback')
def feedback_dashboard():
    """Dashboard for loan outcome feedback and training data"""
    return render_template('ml/feedback.html')

@ml_bp.route('/api/loan-outcomes', methods=['GET'])
def get_loan_outcomes():
    """Get loan outcomes for feedback training"""
    try:
        outcomes_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'loan_outcomes.json')
        
        try:
            with open(outcomes_path, 'r') as f:
                outcomes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            outcomes = []
        
        return jsonify({
            'status': 'success',
            'outcomes': outcomes
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get outcomes: {str(e)}'
        }), 500

@ml_bp.route('/api/record-outcome', methods=['POST'])
def record_loan_outcome():
    """Record loan outcome for training feedback"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assessment_id', 'selected_offer', 'funding_decision', 'actual_offer']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Create outcome record
        outcome = {
            'id': f"outcome_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'assessment_id': data['assessment_id'],
            'selected_offer': data['selected_offer'],
            'funding_decision': data['funding_decision'],  # 'approved', 'declined', 'pending'
            'actual_offer': data['actual_offer'],  # Modified offer details
            'payment_performance': data.get('payment_performance'),  # 'on_time', 'late', 'default', 'pending'
            'loan_status': data.get('loan_status'),  # 'active', 'paid_in_full', 'defaulted', 'closed'
            'notes': data.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save to file
        outcomes_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'loan_outcomes.json')
        os.makedirs(os.path.dirname(outcomes_path), exist_ok=True)
        
        try:
            with open(outcomes_path, 'r') as f:
                outcomes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            outcomes = []
        
        outcomes.append(outcome)
        
        with open(outcomes_path, 'w') as f:
            json.dump(outcomes, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Loan outcome recorded successfully',
            'outcome_id': outcome['id']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to record outcome: {str(e)}'
        }), 500

@ml_bp.route('/api/update-outcome/<outcome_id>', methods=['PUT'])
def update_loan_outcome(outcome_id):
    """Update existing loan outcome"""
    try:
        data = request.get_json()
        outcomes_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'loan_outcomes.json')
        
        try:
            with open(outcomes_path, 'r') as f:
                outcomes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            outcomes = []
        
        # Find and update outcome
        outcome_found = False
        for outcome in outcomes:
            if outcome['id'] == outcome_id:
                outcome.update({
                    'payment_performance': data.get('payment_performance', outcome.get('payment_performance')),
                    'loan_status': data.get('loan_status', outcome.get('loan_status')),
                    'notes': data.get('notes', outcome.get('notes')),
                    'updated_at': datetime.now().isoformat()
                })
                outcome_found = True
                break
        
        if not outcome_found:
            return jsonify({
                'status': 'error',
                'message': 'Outcome not found'
            }), 404
        
        with open(outcomes_path, 'w') as f:
            json.dump(outcomes, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Outcome updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to update outcome: {str(e)}'
        }), 500

@ml_bp.route('/api/retrain-model', methods=['POST'])
def retrain_with_feedback():
    """Retrain model using outcome feedback data"""
    try:
        data = request.get_json()
        model_type = data.get('model_type', 'feedback_enhanced')
        
        # Load outcomes for training
        outcomes_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'loan_outcomes.json')
        
        try:
            with open(outcomes_path, 'r') as f:
                outcomes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            outcomes = []
        
        # Filter outcomes with payment performance data
        training_outcomes = [o for o in outcomes if o.get('payment_performance')]
        
        if len(training_outcomes) < 10:
            return jsonify({
                'status': 'error',
                'message': 'Insufficient training data. Need at least 10 outcomes with payment performance.'
            }), 400
        
        # Create training job with feedback data
        job = {
            'id': f"feedback_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'model_type': model_type,
            'data_source': 'loan_outcomes_feedback',
            'training_samples': len(training_outcomes),
            'status': 'training',
            'progress': 0,
            'accuracy': 0,
            'loss': 0,
            'feedback_metrics': {
                'on_time_payments': len([o for o in training_outcomes if o.get('payment_performance') == 'on_time']),
                'late_payments': len([o for o in training_outcomes if o.get('payment_performance') == 'late']),
                'defaults': len([o for o in training_outcomes if o.get('payment_performance') == 'default'])
            },
            'started_at': datetime.now().isoformat()
        }
        
        # Save training job
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
            'message': f'Feedback training started with {len(training_outcomes)} outcome samples'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start feedback training: {str(e)}'
        }), 500
