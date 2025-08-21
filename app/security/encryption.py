
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets

class DataEncryption:
    def __init__(self):
        self.key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'encryption_key.key')
        self.salt_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'salt.key')
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Generate or load encryption key"""
        if not os.path.exists(self.key_file) or not os.path.exists(self.salt_file):
            self._generate_new_key()
        
        with open(self.salt_file, 'rb') as f:
            self.salt = f.read()
        
        # Derive key from environment variable or generated key
        password = os.environ.get('ENCRYPTION_PASSWORD', 'default_password_change_in_production').encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)
    
    def _generate_new_key(self):
        """Generate new encryption components"""
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        # Generate salt
        salt = os.urandom(16)
        with open(self.salt_file, 'wb') as f:
            f.write(salt)
        
        # Generate key file marker
        with open(self.key_file, 'w') as f:
            f.write('encryption_key_initialized')
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(self.cipher.encrypt(data)).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            return self.cipher.decrypt(encrypted_bytes).decode()
        except:
            return None
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + pwdhash.hex()
    
    def verify_password(self, password, stored_hash):
        """Verify password against hash"""
        salt = stored_hash[:64]
        stored_password = stored_hash[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return pwdhash.hex() == stored_password

encryption = DataEncryption()
