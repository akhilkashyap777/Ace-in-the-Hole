# simple_encryption.py - Clean and simple file encryption
import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SimpleEncryption:
    def __init__(self, pin):
        # Generate key from PIN
        salt = b'vault2024'  # Fixed salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_file(self, source_path, target_path):
        """Encrypt file from source to target"""
        try:
            with open(source_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.cipher.encrypt(data)
            
            with open(target_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except:
            return False
    
    def decrypt_file(self, encrypted_path, target_path):
        """Decrypt file from encrypted to target"""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            data = self.cipher.decrypt(encrypted_data)
            
            with open(target_path, 'wb') as f:
                f.write(data)
            
            return True
        except:
            return False
    
    def decrypt_to_memory(self, encrypted_path):
        """Decrypt file and return data in memory"""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            return self.cipher.decrypt(encrypted_data)
        except:
            return None

def encrypt_and_store(source_path, vault_dir, filename, pin):
    """Simple function to encrypt and store a file"""
    try:
        os.makedirs(vault_dir, exist_ok=True)
        
        # Create encrypted filename
        name, ext = os.path.splitext(filename)
        encrypted_name = f"{name}.vault"
        target_path = os.path.join(vault_dir, encrypted_name)
        
        # Handle name conflicts
        counter = 1
        while os.path.exists(target_path):
            encrypted_name = f"{name}_{counter}.vault"
            target_path = os.path.join(vault_dir, encrypted_name)
            counter += 1
        
        # Encrypt file
        encryptor = SimpleEncryption(pin)
        if encryptor.encrypt_file(source_path, target_path):
            # Save metadata
            metadata_file = os.path.join(vault_dir, "file_info.json")
            metadata = {}
            
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except:
                    metadata = {}
            
            metadata[encrypted_name] = {
                'original_name': filename,
                'original_ext': ext
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
            
            return {"success": True, "encrypted_path": target_path}
        
        return {"success": False, "error": "Encryption failed"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def decrypt_for_viewing(encrypted_path, pin):
    """Decrypt file to temp location for viewing"""
    try:
        import tempfile
        
        # Get original name from metadata
        vault_dir = os.path.dirname(encrypted_path)
        encrypted_name = os.path.basename(encrypted_path)
        
        metadata_file = os.path.join(vault_dir, "file_info.json")
        original_name = encrypted_name.replace('.vault', '')
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                if encrypted_name in metadata:
                    original_name = metadata[encrypted_name]['original_name']
            except:
                pass
        
        # Create temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"vault_temp_{original_name}")
        
        # Decrypt
        encryptor = SimpleEncryption(pin)
        if encryptor.decrypt_file(encrypted_path, temp_path):
            return temp_path
        
        return None
    
    except:
        return None

def get_encrypted_files(vault_dir):
    """Get list of encrypted files"""
    files = []
    
    if not os.path.exists(vault_dir):
        return files
    
    # Load metadata
    metadata_file = os.path.join(vault_dir, "file_info.json")
    metadata = {}
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except:
            pass
    
    # List vault files
    for filename in os.listdir(vault_dir):
        if filename.endswith('.vault'):
            file_path = os.path.join(vault_dir, filename)
            
            # Get display name
            display_name = filename.replace('.vault', '')
            if filename in metadata:
                display_name = metadata[filename]['original_name']
            
            files.append({
                'encrypted_path': file_path,
                'display_name': display_name,
                'file_size': os.path.getsize(file_path)
            })
    
    return files