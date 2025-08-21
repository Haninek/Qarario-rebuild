
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import session, request
import json

class SecureSessionManager:
    def __init__(self):
        self.session_timeout = 30  # 30 minutes
        self.sessions_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'active_sessions.json')
        self._ensure_sessions_file()
    
    def _ensure_sessions_file(self):
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump({}, f)
    
    def create_session(self, user_id, user_agent, ip_address):
        """Create a secure session with token and metadata"""
        session_token = secrets.token_urlsafe(64)
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        session_data = {
            'user_id': user_id,
            'token': session_token,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'user_agent': user_agent,
            'ip_address': ip_address,
            'expires_at': (datetime.utcnow() + timedelta(minutes=self.session_timeout)).isoformat()
        }
        
        # Store in Flask session
        session['session_id'] = session_id
        session['user_id'] = user_id
        session['session_token'] = session_token
        
        # Store in persistent storage
        self._store_session(session_id, session_data)
        
        return session_id
    
    def validate_session(self):
        """Validate current session and check for hijacking"""
        if 'session_id' not in session or 'session_token' not in session:
            return False
        
        session_id = session['session_id']
        session_token = session['session_token']
        
        stored_session = self._get_session(session_id)
        if not stored_session:
            return False
        
        # Check token match
        if stored_session['token'] != session_token:
            self.destroy_session(session_id)
            return False
        
        # Check expiration
        expires_at = datetime.fromisoformat(stored_session['expires_at'])
        if datetime.utcnow() > expires_at:
            self.destroy_session(session_id)
            return False
        
        # Check for session hijacking
        if stored_session['user_agent'] != request.headers.get('User-Agent', ''):
            self.destroy_session(session_id)
            return False
        
        # Update last activity
        stored_session['last_activity'] = datetime.utcnow().isoformat()
        stored_session['expires_at'] = (datetime.utcnow() + timedelta(minutes=self.session_timeout)).isoformat()
        self._store_session(session_id, stored_session)
        
        return True
    
    def destroy_session(self, session_id=None):
        """Destroy session securely"""
        if not session_id:
            session_id = session.get('session_id')
        
        if session_id:
            self._remove_session(session_id)
        
        session.clear()
    
    def _store_session(self, session_id, session_data):
        try:
            with open(self.sessions_file, 'r') as f:
                sessions = json.load(f)
        except:
            sessions = {}
        
        sessions[session_id] = session_data
        
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def _get_session(self, session_id):
        try:
            with open(self.sessions_file, 'r') as f:
                sessions = json.load(f)
            return sessions.get(session_id)
        except:
            return None
    
    def _remove_session(self, session_id):
        try:
            with open(self.sessions_file, 'r') as f:
                sessions = json.load(f)
            
            if session_id in sessions:
                del sessions[session_id]
                
                with open(self.sessions_file, 'w') as f:
                    json.dump(sessions, f, indent=2)
        except:
            pass

session_manager = SecureSessionManager()
