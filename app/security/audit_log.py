
import json
import os
from datetime import datetime
from flask import request, session

class AuditLogger:
    def __init__(self):
        self.audit_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'audit.log')
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        os.makedirs(os.path.dirname(self.audit_file), exist_ok=True)
    
    def log_event(self, event_type, user_id=None, details=None, severity='INFO'):
        """Log security and access events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id or session.get('user_id', 'anonymous'),
            'ip_address': request.remote_addr if request else 'system',
            'user_agent': request.headers.get('User-Agent', '') if request else 'system',
            'endpoint': request.endpoint if request else 'system',
            'method': request.method if request else 'system',
            'severity': severity,
            'details': details or {}
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_login_attempt(self, user_id, success=True, reason=None):
        """Log login attempts"""
        self.log_event(
            'LOGIN_ATTEMPT',
            user_id,
            {'success': success, 'reason': reason},
            'INFO' if success else 'WARNING'
        )
    
    def log_data_access(self, user_id, data_type, action):
        """Log data access events"""
        self.log_event(
            'DATA_ACCESS',
            user_id,
            {'data_type': data_type, 'action': action}
        )
    
    def log_security_violation(self, violation_type, details):
        """Log security violations"""
        self.log_event(
            'SECURITY_VIOLATION',
            details=details,
            severity='CRITICAL'
        )

audit_logger = AuditLogger()
