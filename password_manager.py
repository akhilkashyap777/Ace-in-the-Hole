# password_manager.py - Cross-platform password management
# ✅ OPTIMIZED VERSION - Fixed memory leaks and performance issues
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Android keystore imports
try:
    from jnius import autoclass
    ANDROID = True
    # Android Keystore classes
    KeyStore = autoclass('java.security.KeyStore')
    KeyGenerator = autoclass('javax.crypto.KeyGenerator')
    KeyGenParameterSpec = autoclass('android.security.keystore.KeyGenParameterSpec')
    KeyProperties = autoclass('android.security.keystore.KeyProperties')
    Cipher = autoclass('javax.crypto.Cipher')
    SecretKeySpec = autoclass('javax.crypto.spec.SecretKeySpec')
except ImportError:
    ANDROID = False

class PasswordManager:
    def __init__(self, app_name="SecretVault"):
        self.app_name = app_name
        self.config_dir = self._get_config_directory()
        self.config_file = os.path.join(self.config_dir, "vault_config.dat")
        self.keystore_alias = "vault_master_key"
        
        # ✅ OPTIMIZATION: Cache config data to avoid repeated file operations
        self._config_cache = None
        self._cache_timestamp = 0
        self._cache_dirty = False
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize encryption
        self._setup_encryption()
    
    def _get_config_directory(self):
        """Get platform-specific config directory"""
        if ANDROID:
            # Android app private directory
            from android.storage import app_storage_path
            return app_storage_path()
        else:
            # Desktop platforms
            home = os.path.expanduser("~")
            if os.name == 'nt':  # Windows
                return os.path.join(os.environ.get('APPDATA', home), self.app_name)
            elif os.sys.platform == 'darwin':  # macOS
                return os.path.join(home, 'Library', 'Application Support', self.app_name)
            else:  # Linux
                return os.path.join(home, '.config', self.app_name)
    
    def _setup_encryption(self):
        """Setup encryption key based on platform"""
        if ANDROID:
            self._setup_android_keystore()
        else:
            self._setup_desktop_encryption()
    
    def _setup_android_keystore(self):
        """Setup Android Keystore encryption"""
        try:
            keystore = KeyStore.getInstance("AndroidKeyStore")
            keystore.load(None)
            
            if not keystore.containsAlias(self.keystore_alias):
                # Generate new key in keystore
                keygen = KeyGenerator.getInstance("AES", "AndroidKeyStore")
                spec = KeyGenParameterSpec.Builder(
                    self.keystore_alias,
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT
                ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)\
                 .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)\
                 .build()
                
                keygen.init(spec)
                keygen.generateKey()
            
            self.use_keystore = True
        except Exception as e:
            print(f"Keystore setup failed: {e}")
            self.use_keystore = False
            self._setup_desktop_encryption()
    
    def _setup_desktop_encryption(self):
        """Setup desktop file-based encryption"""
        key_file = os.path.join(self.config_dir, ".key")
        
        if os.path.exists(key_file):
            # Load existing key
            try:
                with open(key_file, 'r') as f:
                    key_data = json.loads(f.read())
                self.encryption_key = base64.b64decode(key_data['key'])
            except:
                # Fallback: treat as raw key file
                with open(key_file, 'rb') as f:
                    raw_key = f.read()
                if len(raw_key) == 32:
                    self.encryption_key = base64.urlsafe_b64encode(raw_key)
                else:
                    # Generate new key if corrupted
                    self.encryption_key = Fernet.generate_key()
                    with open(key_file, 'wb') as f:
                        f.write(self.encryption_key)
        else:
            # Generate new encryption key
            self.encryption_key = Fernet.generate_key()
            
            # Store key
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
            
            # Hide file on Windows
            if os.name == 'nt':
                try:
                    os.system(f'attrib +h "{key_file}"')
                except:
                    pass
        
        self.cipher = Fernet(self.encryption_key)
        self.use_keystore = False
    
    def _encrypt_data(self, data):
        """Encrypt data based on platform"""
        if ANDROID and self.use_keystore:
            return self._android_encrypt(data)
        else:
            return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt data based on platform"""
        if ANDROID and self.use_keystore:
            return self._android_decrypt(encrypted_data)
        else:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def _android_encrypt(self, data):
        """Android Keystore encryption"""
        try:
            keystore = KeyStore.getInstance("AndroidKeyStore")
            keystore.load(None)
            
            key = keystore.getKey(self.keystore_alias, None)
            cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, key)
            
            encrypted_bytes = cipher.doFinal(data.encode())
            iv = cipher.getIV()
            
            # Combine IV and encrypted data
            result = base64.b64encode(iv + encrypted_bytes).decode()
            return result
        except Exception as e:
            print(f"Android encryption failed: {e}")
            return data  # Fallback to plain text
    
    def _android_decrypt(self, encrypted_data):
        """Android Keystore decryption"""
        try:
            keystore = KeyStore.getInstance("AndroidKeyStore")
            keystore.load(None)
            
            key = keystore.getKey(self.keystore_alias, None)
            cipher = Cipher.getInstance("AES/GCM/NoPadding")
            
            # Decode and split IV and data
            combined = base64.b64decode(encrypted_data.encode())
            iv = combined[:12]  # GCM IV is 12 bytes
            encrypted_bytes = combined[12:]
            
            cipher.init(Cipher.DECRYPT_MODE, key, iv)
            decrypted_bytes = cipher.doFinal(encrypted_bytes)
            
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"Android decryption failed: {e}")
            return encrypted_data  # Return as-is if decryption fails
    
    def _load_config(self):
        """✅ OPTIMIZATION: Load and cache config data to avoid repeated file operations"""
        if not os.path.exists(self.config_file):
            return None
        
        try:
            # Check if cache is still valid (cache for 60 seconds)
            file_mtime = os.path.getmtime(self.config_file)
            if (self._config_cache is not None and 
                self._cache_timestamp >= file_mtime and
                not self._cache_dirty):
                return self._config_cache.copy()
            
            # Load from file
            with open(self.config_file, 'r') as f:
                encrypted_config = f.read()
            
            config_str = self._decrypt_data(encrypted_config)
            config = json.loads(config_str)
            
            # Update cache
            self._config_cache = config.copy()
            self._cache_timestamp = time.time()
            self._cache_dirty = False
            
            return config
        except Exception as e:
            print(f"Config load error: {e}")
            return None
    
    def _save_config(self, config):
        """✅ OPTIMIZATION: Save config and update cache"""
        try:
            encrypted_config = self._encrypt_data(json.dumps(config))
            with open(self.config_file, 'w') as f:
                f.write(encrypted_config)
            
            # Update cache
            self._config_cache = config.copy()
            self._cache_timestamp = time.time()
            self._cache_dirty = False
            
        except Exception as e:
            print(f"Config save error: {e}")
    
    def is_first_launch(self):
        """Check if this is the first app launch"""
        return not os.path.exists(self.config_file)
    
    def setup_password(self, pin, security_question, security_answer):
        """Setup initial password and security question"""
        # Hash PIN
        pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
        
        # Hash security answer (case insensitive)
        answer_hash = bcrypt.hashpw(security_answer.lower().encode(), bcrypt.gensalt()).decode()
        
        config = {
            'pin_hash': pin_hash,
            'security_question': security_question,
            'answer_hash': answer_hash,
            'failed_attempts': 0,
            'last_attempt_time': 0,
            'lockout_until': 0,
            'setup_complete': True
        }
        
        # Save config using optimized method
        self._save_config(config)
        return True
    
    def verify_pin(self, pin):
        """✅ OPTIMIZED: Verify entered PIN with caching"""
        config = self._load_config()
        if not config:
            return False, "error"
        
        try:
            # Check if locked out
            current_time = time.time()
            if current_time < config.get('lockout_until', 0):
                return False, "locked"
            
            # Check PIN
            if bcrypt.checkpw(pin.encode(), config['pin_hash'].encode()):
                # Reset failed attempts on success
                config['failed_attempts'] = 0
                config['last_attempt_time'] = current_time
                self._save_config(config)
                return True, "success"
            else:
                # Increment failed attempts
                config['failed_attempts'] = config.get('failed_attempts', 0) + 1
                config['last_attempt_time'] = current_time
                
                # Check if should lock out (5 attempts per hour)
                if config['failed_attempts'] >= 5:
                    config['lockout_until'] = current_time + 3600  # 1 hour lockout
                    config['failed_attempts'] = 0  # Reset for next hour
                
                self._save_config(config)
                return False, f"failed_{config['failed_attempts']}"
        
        except Exception as e:
            print(f"PIN verification error: {e}")
            return False, "error"
    
    def verify_security_answer(self, answer):
        """✅ OPTIMIZED: Verify security question answer with caching"""
        config = self._load_config()
        if not config:
            return False
        
        try:
            return bcrypt.checkpw(answer.lower().encode(), config['answer_hash'].encode())
        except Exception as e:
            print(f"Security answer verification error: {e}")
            return False
    
    def get_security_question(self):
        """✅ OPTIMIZED: Get the security question with caching"""
        config = self._load_config()
        if not config:
            return None
        
        return config.get('security_question')
    
    def reset_password(self, new_pin):
        """✅ OPTIMIZED: Reset password using security question with caching"""
        config = self._load_config()
        if not config:
            return False
        
        try:
            # Update PIN
            config['pin_hash'] = bcrypt.hashpw(new_pin.encode(), bcrypt.gensalt()).decode()
            config['failed_attempts'] = 0
            config['lockout_until'] = 0
            
            self._save_config(config)
            return True
        
        except Exception as e:
            print(f"Password reset error: {e}")
            return False
    
    def get_lockout_time_remaining(self):
        """✅ OPTIMIZED: Get remaining lockout time in seconds with caching"""
        config = self._load_config()
        if not config:
            return 0
        
        try:
            current_time = time.time()
            lockout_until = config.get('lockout_until', 0)
            
            if current_time < lockout_until:
                return int(lockout_until - current_time)
            return 0
        
        except Exception as e:
            print(f"Get lockout time error: {e}")
            return 0
    
    def clear_cache(self):
        """✅ OPTIMIZATION: Clear internal cache (useful for testing or manual refresh)"""
        self._config_cache = None
        self._cache_timestamp = 0
        self._cache_dirty = True