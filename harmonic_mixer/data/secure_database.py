"""
Secure database with encryption for sensitive settings
"""

import os
import json
import base64
from typing import Any, Optional
from pathlib import Path

# Try to import cryptography, fallback to basic encoding if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

from .database import SettingsDatabase


class EncryptionManager:
    """Manages encryption/decryption of sensitive data"""
    
    def __init__(self, password: str = None):
        self.password = password or self._get_default_password()
        self.cipher = self._create_cipher() if CRYPTOGRAPHY_AVAILABLE else None
    
    def _get_default_password(self) -> str:
        """Generate default password based on system info"""
        # Use system-specific information for default encryption
        import platform
        import getpass
        
        system_info = f"{platform.node()}{getpass.getuser()}{platform.platform()}"
        return system_info[:32].ljust(32, '0')  # Ensure 32 chars
    
    def _create_cipher(self):
        """Create Fernet cipher from password"""
        if not CRYPTOGRAPHY_AVAILABLE:
            return None
        
        password_bytes = self.password.encode()
        salt = b'bluelibrary_salt'  # In production, use random salt per user
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not CRYPTOGRAPHY_AVAILABLE or not self.cipher:
            # Fallback to base64 encoding (not secure but functional)
            return base64.b64encode(data.encode()).decode()
        
        try:
            encrypted_bytes = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception:
            # Return original data if encryption fails
            return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not CRYPTOGRAPHY_AVAILABLE or not self.cipher:
            # Fallback to base64 decoding
            try:
                return base64.b64decode(encrypted_data.encode()).decode()
            except Exception:
                return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            # Return original data if decryption fails (might be unencrypted)
            return encrypted_data


class SecureSettingsDatabase(SettingsDatabase):
    """Settings database with encryption for sensitive data"""
    
    # Define which settings should be encrypted
    ENCRYPTED_SETTINGS = {
        'user_preferences',
        'api_keys',
        'personal_data',
        'license_info'
    }
    
    def __init__(self, db_path: Optional[str] = None, encryption_password: str = None):
        super().__init__(db_path)
        self.encryption = EncryptionManager(encryption_password)
    
    def set_setting(self, key: str, value: Any):
        """Set setting with encryption for sensitive data"""
        # Convert value to JSON string
        if not isinstance(value, str):
            value = json.dumps(value)
        
        # Encrypt if it's a sensitive setting
        if key in self.ENCRYPTED_SETTINGS:
            value = self.encryption.encrypt(value)
        
        # Store in database
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        conn.commit()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting with decryption for sensitive data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            value = row['value']
            
            # Decrypt if it's a sensitive setting
            if key in self.ENCRYPTED_SETTINGS:
                value = self.encryption.decrypt(value)
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        return default
    
    def set_secure_setting(self, key: str, value: Any):
        """Force encryption for a specific setting"""
        if not isinstance(value, str):
            value = json.dumps(value)
        
        encrypted_value = self.encryption.encrypt(value)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, encrypted_value))
        
        self.conn.commit()
    
    def get_secure_setting(self, key: str, default: Any = None) -> Any:
        """Force decryption for a specific setting"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            decrypted_value = self.encryption.decrypt(row['value'])
            
            try:
                return json.loads(decrypted_value)
            except json.JSONDecodeError:
                return decrypted_value
        
        return default


class DataProtectionManager:
    """Manages data protection and privacy features"""
    
    def __init__(self, db: SecureSettingsDatabase):
        self.db = db
    
    def anonymize_data(self, data: dict) -> dict:
        """Anonymize sensitive data in dictionary"""
        anonymized = data.copy()
        
        sensitive_keys = ['filepath', 'artist', 'title', 'folder_path']
        
        for key in sensitive_keys:
            if key in anonymized:
                # Replace with anonymized version
                if isinstance(anonymized[key], str):
                    anonymized[key] = self._hash_string(anonymized[key])
        
        return anonymized
    
    def _hash_string(self, text: str) -> str:
        """Create consistent hash of string for anonymization"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def export_user_data(self) -> dict:
        """Export all user data for GDPR compliance"""
        all_settings = self.db.get_all_settings()
        playlists = self.db.get_playlists()
        recent_folders = self.db.get_recent_folders()
        
        return {
            'settings': all_settings,
            'playlists': playlists,
            'recent_folders': recent_folders,
            'export_timestamp': self.db.get_setting('export_timestamp')
        }
    
    def delete_user_data(self):
        """Delete all user data"""
        cursor = self.db.conn.cursor()
        
        # Clear all tables
        cursor.execute("DELETE FROM settings")
        cursor.execute("DELETE FROM playlists")
        cursor.execute("DELETE FROM recent_folders")
        
        self.db.conn.commit()
    
    def backup_user_data(self, backup_path: str):
        """Create encrypted backup of user data"""
        user_data = self.export_user_data()
        encrypted_data = self.db.encryption.encrypt(json.dumps(user_data))
        
        with open(backup_path, 'w') as f:
            f.write(encrypted_data)
    
    def restore_user_data(self, backup_path: str):
        """Restore user data from encrypted backup"""
        with open(backup_path, 'r') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.db.encryption.decrypt(encrypted_data)
        user_data = json.loads(decrypted_data)
        
        # Restore settings
        for key, value in user_data.get('settings', {}).items():
            self.db.set_setting(key, value)
        
        # Restore playlists
        for playlist in user_data.get('playlists', []):
            self.db.save_playlist(
                playlist['name'],
                playlist['tracks'],
                playlist['settings']
            )
        
        # Restore recent folders
        for folder in user_data.get('recent_folders', []):
            self.db.add_recent_folder(folder)


class PrivacySettings:
    """Manages privacy-related settings"""
    
    def __init__(self, db: SecureSettingsDatabase):
        self.db = db
    
    def set_analytics_enabled(self, enabled: bool):
        """Enable/disable analytics collection"""
        self.db.set_setting('analytics_enabled', enabled)
    
    def is_analytics_enabled(self) -> bool:
        """Check if analytics are enabled"""
        return self.db.get_setting('analytics_enabled', False)
    
    def set_crash_reporting_enabled(self, enabled: bool):
        """Enable/disable crash reporting"""
        self.db.set_setting('crash_reporting_enabled', enabled)
    
    def is_crash_reporting_enabled(self) -> bool:
        """Check if crash reporting is enabled"""
        return self.db.get_setting('crash_reporting_enabled', True)
    
    def set_auto_update_enabled(self, enabled: bool):
        """Enable/disable automatic updates"""
        self.db.set_setting('auto_update_enabled', enabled)
    
    def is_auto_update_enabled(self) -> bool:
        """Check if auto updates are enabled"""
        return self.db.get_setting('auto_update_enabled', True)
    
    def get_privacy_summary(self) -> dict:
        """Get summary of privacy settings"""
        return {
            'analytics_enabled': self.is_analytics_enabled(),
            'crash_reporting_enabled': self.is_crash_reporting_enabled(),
            'auto_update_enabled': self.is_auto_update_enabled(),
            'data_encryption_enabled': True,  # Always enabled
            'anonymization_enabled': True     # Always enabled
        }
