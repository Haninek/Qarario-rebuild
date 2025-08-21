
import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from app.security.encryption import encryption

class User:
    def __init__(self, user_id, username, email, subscription_tier='free', api_access_enabled=False):
        self.user_id = user_id
        self.username = username
        self.email = encryption.encrypt_data(email)  # Encrypt PII
        self.subscription_tier = subscription_tier
        self.api_access_enabled = api_access_enabled
        self.api_key = None
        self.api_token = None
        self.password_hash = None
        self.created_at = datetime.utcnow().isoformat()
        self.last_login = None
        self.failed_login_attempts = 0
        self.account_locked = False
        
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,  # Already encrypted
            'subscription_tier': self.subscription_tier,
            'api_access_enabled': self.api_access_enabled,
            'api_key': self.api_key,
            'api_token': self.api_token,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'failed_login_attempts': self.failed_login_attempts,
            'account_locked': self.account_locked
        }
    
    def get_decrypted_email(self):
        """Get decrypted email for display"""
        return encryption.decrypt_data(self.email) if self.email else None
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = encryption.hash_password(password)
    
    def verify_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return False
        return encryption.verify_password(password, self.password_hash)
    
    @classmethod
    def from_dict(cls, data):
        user = cls.__new__(cls)  # Create without calling __init__
        user.user_id = data['user_id']
        user.username = data['username']
        user.email = data['email']  # Already encrypted in storage
        user.subscription_tier = data.get('subscription_tier', 'free')
        user.api_access_enabled = data.get('api_access_enabled', False)
        user.api_key = data.get('api_key')
        user.api_token = data.get('api_token')
        user.password_hash = data.get('password_hash')
        user.created_at = data.get('created_at', datetime.utcnow().isoformat())
        user.last_login = data.get('last_login')
        user.failed_login_attempts = data.get('failed_login_attempts', 0)
        user.account_locked = data.get('account_locked', False)
        return user

class UserManager:
    def __init__(self):
        self.users_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'users.json')
        self.api_keys_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'api_keys.json')
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
                
        if not os.path.exists(self.api_keys_file):
            with open(self.api_keys_file, 'w') as f:
                json.dump({}, f)
    
    def load_users(self):
        try:
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
                return {uid: User.from_dict(data) for uid, data in users_data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_users(self, users):
        users_data = {uid: user.to_dict() for uid, user in users.items()}
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def load_api_keys(self):
        try:
            with open(self.api_keys_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_api_keys(self, api_keys):
        with open(self.api_keys_file, 'w') as f:
            json.dump(api_keys, f, indent=2)
    
    def create_user(self, user_id, username, email, subscription_tier='free'):
        users = self.load_users()
        if user_id in users:
            return users[user_id]
        
        user = User(user_id, username, email, subscription_tier)
        users[user_id] = user
        self.save_users(users)
        return user
    
    def get_user(self, user_id):
        users = self.load_users()
        return users.get(user_id)
    
    def update_subscription(self, user_id, subscription_tier):
        users = self.load_users()
        if user_id in users:
            users[user_id].subscription_tier = subscription_tier
            # Enable API access for premium subscribers
            if subscription_tier in ['premium', 'enterprise']:
                users[user_id].api_access_enabled = True
            else:
                users[user_id].api_access_enabled = False
                users[user_id].api_key = None
                users[user_id].api_token = None
            self.save_users(users)
            return users[user_id]
        return None
    
    def toggle_api_access(self, user_id, enabled):
        users = self.load_users()
        if user_id in users:
            user = users[user_id]
            # Only allow API access for premium/enterprise subscribers
            if user.subscription_tier in ['premium', 'enterprise']:
                user.api_access_enabled = enabled
                if not enabled:
                    user.api_key = None
                    user.api_token = None
                    # Remove from API keys mapping
                    api_keys = self.load_api_keys()
                    keys_to_remove = [k for k, v in api_keys.items() if v == user_id]
                    for key in keys_to_remove:
                        del api_keys[key]
                    self.save_api_keys(api_keys)
                self.save_users(users)
                return user
        return None
    
    def generate_api_credentials(self, user_id):
        users = self.load_users()
        if user_id not in users:
            return None
        
        user = users[user_id]
        if not user.api_access_enabled or user.subscription_tier not in ['premium', 'enterprise']:
            return None
        
        # Generate API key and token
        api_key = f"qr_{secrets.token_urlsafe(32)}"
        api_token = secrets.token_urlsafe(64)
        
        # Store credentials
        user.api_key = api_key
        user.api_token = hashlib.sha256(api_token.encode()).hexdigest()
        
        # Update API keys mapping
        api_keys = self.load_api_keys()
        api_keys[api_key] = user_id
        
        self.save_users(users)
        self.save_api_keys(api_keys)
        
        return {
            'api_key': api_key,
            'api_token': api_token,  # Return plain token only once
            'user_id': user_id
        }
    
    def validate_api_credentials(self, api_key, api_token):
        api_keys = self.load_api_keys()
        if api_key not in api_keys:
            return None
        
        user_id = api_keys[api_key]
        users = self.load_users()
        if user_id not in users:
            return None
        
        user = users[user_id]
        if not user.api_access_enabled:
            return None
        
        # Validate token
        token_hash = hashlib.sha256(api_token.encode()).hexdigest()
        if user.api_token != token_hash:
            return None
        
        return user

# Global instance
user_manager = UserManager()
