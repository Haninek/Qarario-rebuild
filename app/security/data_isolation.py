
from functools import wraps
from flask import session, request, jsonify
from app.security.audit_log import audit_logger

class DataIsolation:
    def __init__(self):
        pass
    
    def ensure_user_data_isolation(self, f):
        """Decorator to ensure users can only access their own data"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = session.get('user_id')
            
            # Check for any user_id parameters in request
            request_user_id = (
                request.args.get('user_id') or 
                request.form.get('user_id') or
                (request.get_json() or {}).get('user_id') if request.is_json else None
            )
            
            # If a user_id is specified and it's not the current user's, deny access
            if request_user_id and request_user_id != current_user_id:
                audit_logger.log_security_violation('DATA_ISOLATION_VIOLATION', {
                    'current_user': current_user_id,
                    'requested_user': request_user_id,
                    'endpoint': request.endpoint
                })
                return jsonify({
                    'error': 'Access denied: You can only access your own data',
                    'status': 'forbidden'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def filter_user_data(self, data, user_id_field='user_id'):
        """Filter data to only include current user's records"""
        current_user_id = session.get('user_id')
        
        if isinstance(data, list):
            return [item for item in data if item.get(user_id_field) == current_user_id]
        elif isinstance(data, dict):
            if data.get(user_id_field) == current_user_id:
                return data
            else:
                return {}
        
        return data

data_isolation = DataIsolation()
