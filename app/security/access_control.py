
from functools import wraps
from flask import request, jsonify, session, abort
from app.models.user import user_manager
from app.security.session import session_manager
import logging

# Set up security logging
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger('security')

class AccessControl:
    def __init__(self):
        self.admin_users = ['admin', 'super_admin']  # Define admin users
        self.restricted_endpoints = ['/admin', '/ml', '/train', '/builder']
    
    def require_login(self, f):
        """Decorator to require user authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session_manager.validate_session():
                security_logger.warning(f"Unauthorized access attempt to {request.endpoint} from {request.remote_addr}")
                return jsonify({'error': 'Authentication required', 'status': 'unauthorized'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    def require_admin(self, f):
        """Decorator to require admin privileges"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session_manager.validate_session():
                return jsonify({'error': 'Authentication required', 'status': 'unauthorized'}), 401
            
            user_id = session.get('user_id')
            if user_id not in self.admin_users:
                security_logger.warning(f"Admin access attempt by non-admin user {user_id} to {request.endpoint}")
                return jsonify({'error': 'Admin privileges required', 'status': 'forbidden'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def require_user_ownership(self, f):
        """Decorator to ensure users can only access their own data"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session_manager.validate_session():
                return jsonify({'error': 'Authentication required', 'status': 'unauthorized'}), 401
            
            # Check if user is trying to access their own data
            current_user_id = session.get('user_id')
            requested_user_id = request.args.get('user_id') or request.form.get('user_id') or kwargs.get('user_id')
            
            if requested_user_id and requested_user_id != current_user_id:
                if current_user_id not in self.admin_users:
                    security_logger.warning(f"User {current_user_id} attempted to access data for user {requested_user_id}")
                    return jsonify({'error': 'Access denied', 'status': 'forbidden'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def log_access(self, f):
        """Decorator to log all access attempts"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id', 'anonymous')
            security_logger.info(f"Access: {user_id} -> {request.endpoint} from {request.remote_addr}")
            return f(*args, **kwargs)
        return decorated_function

access_control = AccessControl()
