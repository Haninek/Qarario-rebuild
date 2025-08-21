
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from app.models.user import user_manager
from app.security.session import session_manager
from app.security.access_control import access_control
from app.security.rate_limiting import rate_limiter
from app.security.input_validation import input_validator
from app.security.audit_log import audit_logger

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
@access_control.require_login
@access_control.log_access
def dashboard():
    user_id = session.get('user_id')
    user = user_manager.get_user(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('user.login'))
    
    audit_logger.log_data_access(user_id, 'user_dashboard', 'view')
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
@rate_limiter.rate_limit('login')
@input_validator.validate_request_data({
    'username': {'type': 'username', 'required': True},
    'password': {'type': 'safe_string', 'required': True}
})
def login():
    if request.method == 'POST':
        username = request.validated_data.get('username')
        password = request.validated_data.get('password')
        
        # Find user by username
        users = user_manager.load_users()
        user = None
        for uid, u in users.items():
            if u.username == username:
                user = u
                break
        
        if not user:
            audit_logger.log_login_attempt(username, False, 'User not found')
            flash('Invalid username or password', 'error')
            return render_template('user/login.html')
        
        # Check if account is locked
        if user.account_locked:
            audit_logger.log_login_attempt(username, False, 'Account locked')
            flash('Account is locked due to too many failed attempts', 'error')
            return render_template('user/login.html')
        
        # Verify password
        if not user.verify_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked = True
            user_manager.save_users(users)
            
            audit_logger.log_login_attempt(username, False, 'Invalid password')
            flash('Invalid username or password', 'error')
            return render_template('user/login.html')
        
        # Successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow().isoformat()
        user_manager.save_users(users)
        
        # Create secure session
        session_id = session_manager.create_session(
            user.user_id,
            request.headers.get('User-Agent', ''),
            request.remote_addr
        )
        
        audit_logger.log_login_attempt(user.user_id, True)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/login.html')

@user_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('user.login'))
