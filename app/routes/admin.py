
from flask import Blueprint, render_template, jsonify, request
from app.models.user import user_manager
import json
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/rules')
def rules():
    rules_path = os.path.join(os.path.dirname(__file__), '..', 'rules', 'finance.json')
    with open(rules_path) as f:
        rules = json.load(f)
    return render_template('admin/rules.html', rules=rules)

@admin_bp.route('/logs')
def logs():
    """Return recent underwriting logs as JSON"""
    try:
        log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
        logs = []
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue  # Skip malformed lines
        
        # Return the most recent 50 logs
        return jsonify(logs[-50:])
    except Exception as e:
        return jsonify([]), 500

@admin_bp.route('/ml-insights')
def ml_insights():
    from underwriting_assistant import analyze_logs
    insights = analyze_logs()
    return render_template('admin/ml_insights.html', insights=insights)

@admin_bp.route('/users')
def get_users():
    """Get all users for admin panel"""
    try:
        users = user_manager.load_users()
        users_list = []
        
        for user_id, user in users.items():
            users_list.append({
                'user_id': user.user_id,
                'username': user.username,
                'email': user.get_decrypted_email(),
                'subscription_tier': user.subscription_tier,
                'api_access_enabled': user.api_access_enabled,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'account_locked': user.account_locked
            })
        
        return jsonify(users_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        email = data.get('email')
        subscription_tier = data.get('subscription_tier', 'free')
        
        if not all([user_id, username, email]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        existing_user = user_manager.get_user(user_id)
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
        
        # Create user
        user = user_manager.create_user(user_id, username, email, subscription_tier)
        
        return jsonify({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.get_decrypted_email(),
            'subscription_tier': user.subscription_tier
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        users = user_manager.load_users()
        
        if user_id not in users:
            return jsonify({'error': 'User not found'}), 404
        
        del users[user_id]
        user_manager.save_users(users)
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user"""
    try:
        data = request.json
        users = user_manager.load_users()
        
        if user_id not in users:
            return jsonify({'error': 'User not found'}), 404
        
        user = users[user_id]
        
        if 'subscription_tier' in data:
            user.subscription_tier = data['subscription_tier']
            # Enable API access for premium subscribers
            if data['subscription_tier'] in ['premium', 'enterprise']:
                user.api_access_enabled = True
            else:
                user.api_access_enabled = False
                user.api_key = None
                user.api_token = None
        
        user_manager.save_users(users)
        
        return jsonify({
            'user_id': user.user_id,
            'username': user.username,
            'subscription_tier': user.subscription_tier,
            'api_access_enabled': user.api_access_enabled
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
