
import re
import html
from flask import request, jsonify
from functools import wraps

class InputValidator:
    def __init__(self):
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'username': re.compile(r'^[a-zA-Z0-9_]{3,20}$'),
            'alphanumeric': re.compile(r'^[a-zA-Z0-9\s]+$'),
            'numeric': re.compile(r'^\d+(\.\d+)?$'),
            'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_.@]+$')
        }
        
        self.dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'eval\(',
            r'exec\(',
            r'system\(',
            r'passthru\(',
            r'shell_exec\(',
            r'SELECT.*FROM',
            r'INSERT.*INTO',
            r'UPDATE.*SET',
            r'DELETE.*FROM',
            r'DROP.*TABLE',
            r'UNION.*SELECT'
        ]
    
    def sanitize_input(self, value):
        """Sanitize input to prevent XSS and injection attacks"""
        if not isinstance(value, str):
            return value
        
        # HTML escape
        value = html.escape(value)
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous input detected: {pattern}")
        
        return value.strip()
    
    def validate_field(self, value, field_type, required=True):
        """Validate field based on type"""
        if not value and required:
            raise ValueError(f"Field is required")
        
        if not value:
            return True
        
        value = self.sanitize_input(str(value))
        
        if field_type in self.patterns:
            if not self.patterns[field_type].match(value):
                raise ValueError(f"Invalid {field_type} format")
        
        return True
    
    def validate_request_data(self, validation_rules):
        """Decorator to validate request data"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    # Get data from request
                    if request.is_json:
                        data = request.get_json()
                    else:
                        data = request.form.to_dict()
                    
                    # Validate each field
                    for field, rules in validation_rules.items():
                        value = data.get(field)
                        field_type = rules.get('type', 'safe_string')
                        required = rules.get('required', False)
                        
                        self.validate_field(value, field_type, required)
                        
                        # Update sanitized value
                        if value:
                            data[field] = self.sanitize_input(str(value))
                    
                    # Update request with sanitized data
                    request.validated_data = data
                    
                except ValueError as e:
                    return jsonify({
                        'error': f'Validation error: {str(e)}',
                        'status': 'validation_error'
                    }), 400
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

input_validator = InputValidator()
