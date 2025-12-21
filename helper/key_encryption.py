import base64
import json
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class KeyEncryption:
    """Handle encryption and decryption of API keys"""
    
    def __init__(self):
        self.key_file = ".key_store"
        self.cipher = self._get_or_create_cipher()
    
    def _get_or_create_cipher(self):
        """Get existing cipher or create new one"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate key from machine-specific data
            key = self._generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Hide the key file on Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.key_file, 0x02)
        
        return Fernet(key)
    
    def _generate_key(self):
        """Generate encryption key based on machine ID"""
        import platform
        import hashlib
        
        # Get machine-specific identifier
        machine_id = f"{platform.node()}_{platform.machine()}_{platform.processor()}"
        
        # Use PBKDF2 to derive a key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'AITranslationBridge2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key
    
    def encrypt_keys_list(self, keys_list):
        """Encrypt a list of API keys"""
        if not keys_list:
            return []
        encrypted_list = []
        for key in keys_list:
            if key:  # Only encrypt non-empty keys
                encrypted = self.encrypt_key(key)
                encrypted_list.append(encrypted)
        return encrypted_list

    def decrypt_keys_list(self, encrypted_list):
        """Decrypt a list of API keys"""
        if not encrypted_list:
            return []
        decrypted_list = []
        for encrypted_key in encrypted_list:
            if encrypted_key:  # Only decrypt non-empty keys
                decrypted = self.decrypt_key(encrypted_key)
                decrypted_list.append(decrypted)
        return decrypted_list

    def encrypt_key(self, api_key):
        """Encrypt a single API key"""
        if not api_key:
            return ""
        try:
            # Check if already encrypted by trying to decrypt
            try:
                decoded = base64.urlsafe_b64decode(api_key.encode())
                self.cipher.decrypt(decoded)
                # If decrypt successful, already encrypted
                return api_key
            except:
                # Not encrypted, proceed to encrypt
                pass

            # Encrypt the key
            encrypted = self.cipher.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return api_key

    def decrypt_key(self, encrypted_key):
        """Decrypt a single API key"""
        if not encrypted_key:
            return ""
        try:
            # Try to decrypt
            decoded = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            # If decryption fails, might be plain text
            print(f"Decryption warning: Key might be plain text")
            return encrypted_key
    
    def mask_key_for_display(self, api_key):
        """Mask API key for display (show first 6 and last 4 characters)"""
        if len(api_key) <= 10:
            return "*" * len(api_key)
        return f"{api_key[:6]}{'*' * (len(api_key) - 10)}{api_key[-4:]}"
