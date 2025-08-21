
import time
import json
import os
from collections import defaultdict
from flask import request, jsonify

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.blocked_ips = set()
        self.rate_limits = {
            'api': {'calls': 100, 'window': 3600},  # 100 calls per hour for API
            'login': {'calls': 5, 'window': 300},   # 5 login attempts per 5 minutes
            'general': {'calls': 1000, 'window': 3600}  # 1000 general requests per hour
        }
        self.blocked_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'blocked_ips.json')
        self._load_blocked_ips()
    
    def _load_blocked_ips(self):
        """Load permanently blocked IPs"""
        try:
            with open(self.blocked_file, 'r') as f:
                data = json.load(f)
                self.blocked_ips = set(data.get('blocked_ips', []))
        except:
            self.blocked_ips = set()
    
    def _save_blocked_ips(self):
        """Save blocked IPs to file"""
        os.makedirs(os.path.dirname(self.blocked_file), exist_ok=True)
        with open(self.blocked_file, 'w') as f:
            json.dump({'blocked_ips': list(self.blocked_ips)}, f)
    
    def is_rate_limited(self, identifier, limit_type='general'):
        """Check if identifier is rate limited"""
        if identifier in self.blocked_ips:
            return True
        
        current_time = time.time()
        limit_config = self.rate_limits.get(limit_type, self.rate_limits['general'])
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < limit_config['window']
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= limit_config['calls']:
            # Block IP if excessive requests
            if len(self.requests[identifier]) > limit_config['calls'] * 2:
                self.blocked_ips.add(identifier)
                self._save_blocked_ips()
            return True
        
        # Record this request
        self.requests[identifier].append(current_time)
        return False
    
    def rate_limit(self, limit_type='general'):
        """Decorator for rate limiting"""
        def decorator(f):
            def decorated_function(*args, **kwargs):
                identifier = request.remote_addr
                
                if self.is_rate_limited(identifier, limit_type):
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'status': 'rate_limited',
                        'retry_after': self.rate_limits[limit_type]['window']
                    }), 429
                
                return f(*args, **kwargs)
            decorated_function.__name__ = f.__name__
            return decorated_function
        return decorator

rate_limiter = RateLimiter()
