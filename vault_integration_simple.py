# vault_integration_simple.py - Clean integration with existing vault
from simple_encryption import encrypt_and_store, decrypt_for_viewing, get_encrypted_files
from simple_search_hide import hide_vault_folders

def add_encryption_to_vault(vault_app):
    """Add encryption to existing vault - SIMPLE VERSION"""
    
    # Hide vault folders from search
    if hasattr(vault_app, 'secure_storage'):
        hide_vault_folders(vault_app.secure_storage.base_dir)
    
    # Add encryption methods to vault app
    vault_app.encrypt_and_store_file = lambda source, file_type, filename, pin: encrypt_and_store(
        source, 
        vault_app.secure_storage.get_vault_directory(file_type), 
        filename, 
        pin
    )
    
    vault_app.decrypt_file_for_view = decrypt_for_viewing
    
    vault_app.get_vault_encrypted_files = lambda file_type: get_encrypted_files(
        vault_app.secure_storage.get_vault_directory(file_type)
    )

def store_file_encrypted(vault_app, source_path, file_type, pin, filename=None):
    """Helper to store file with encryption"""
    if not filename:
        filename = os.path.basename(source_path)
    
    if hasattr(vault_app, 'encrypt_and_store_file'):
        return vault_app.encrypt_and_store_file(source_path, file_type, filename, pin)
    else:
        # Fallback to regular storage
        return vault_app.secure_storage.store_file_securely(source_path, file_type, filename)

def get_files_list(vault_app, file_type):
    """Helper to get encrypted files list"""
    if hasattr(vault_app, 'get_vault_encrypted_files'):
        return vault_app.get_vault_encrypted_files(file_type)
    else:
        # Fallback to regular files
        return []

def decrypt_file(vault_app, encrypted_path, pin):
    """Helper to decrypt file for viewing"""
    if hasattr(vault_app, 'decrypt_file_for_view'):
        return vault_app.decrypt_file_for_view(encrypted_path, pin)
    else:
        return encrypted_path  # Return as-is if no encryption