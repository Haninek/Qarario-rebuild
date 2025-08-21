
from functools import wraps
from flask import request, jsonify
from app.models.user import user_manager

def require_api_auth(f):
    """Decorator to require API authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        api_token = request.headers.get('X-API-Token')
        
        if not api_key or not api_token:
            return jsonify({
                'error': 'API authentication required. Please provide X-API-Key and X-API-Token headers.',
                'status': 'unauthorized'
            }), 401
        
        # Validate credentials
        user = user_manager.validate_api_credentials(api_key, api_token)
        if not user:
            return jsonify({
                'error': 'Invalid API credentials.',
                'status': 'unauthorized'
            }), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def require_subscription(subscription_tiers):
    """Decorator to require specific subscription tiers"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(request, 'current_user', None)
            if not user or user.subscription_tier not in subscription_tiers:
                return jsonify({
                    'error': f'This endpoint requires a subscription. Required tiers: {", ".join(subscription_tiers)}',
                    'status': 'forbidden',
                    'current_tier': user.subscription_tier if user else 'none'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
