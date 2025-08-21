
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from app.models.user import user_manager

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def dashboard():
    # For demo purposes, we'll use session or create a demo user
    user_id = session.get('user_id', 'demo_user')
    username = session.get('username', 'Demo User')
    email = session.get('email', 'demo@example.com')
    
    # Get or create user
    user = user_manager.get_user(user_id)
    if not user:
        user = user_manager.create_user(user_id, username, email, 'free')
    
    return render_template('user/dashboard.html', user=user)

@user_bp.route('/subscription', methods=['GET', 'POST'])
def subscription():
    user_id = session.get('user_id', 'demo_user')
    
    if request.method == 'POST':
        new_tier = request.form.get('subscription_tier')
        if new_tier in ['free', 'premium', 'enterprise']:
            user = user_manager.update_subscription(user_id, new_tier)
            flash(f'Subscription updated to {new_tier}!', 'success')
            return redirect(url_for('user.subscription'))
    
    user = user_manager.get_user(user_id)
    if not user:
        user = user_manager.create_user(user_id, 'Demo User', 'demo@example.com')
    
    return render_template('user/subscription.html', user=user)

@user_bp.route('/api-access', methods=['GET', 'POST'])
def api_access():
    user_id = session.get('user_id', 'demo_user')
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'toggle':
            enabled = request.form.get('enabled') == 'true'
            user = user_manager.toggle_api_access(user_id, enabled)
            if user:
                flash(f'API access {"enabled" if enabled else "disabled"}!', 'success')
            else:
                flash('Failed to update API access. Premium subscription required.', 'error')
        
        elif action == 'generate':
            credentials = user_manager.generate_api_credentials(user_id)
            if credentials:
                return render_template('user/api_credentials.html', credentials=credentials)
            else:
                flash('Failed to generate API credentials. Make sure API access is enabled.', 'error')
        
        return redirect(url_for('user.api_access'))
    
    user = user_manager.get_user(user_id)
    if not user:
        user = user_manager.create_user(user_id, 'Demo User', 'demo@example.com')
    
    return render_template('user/api_access.html', user=user)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple demo login - in production, use proper authentication
        username = request.form.get('username', 'Demo User')
        email = request.form.get('email', 'demo@example.com')
        user_id = f"user_{hash(email) % 10000}"
        
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        
        flash('Logged in successfully!', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/login.html')

@user_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('user.login'))
