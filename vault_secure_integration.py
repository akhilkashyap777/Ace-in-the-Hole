# vault_secure_integration.py - Simple connector between secure_storage.py and your vault modules
"""
This is the "key" that connects secure_storage.py to your existing vault modules.
Much simpler than the original complex version.
"""

from secure_storage import SecureStorage
import os
import shutil

def setup_secure_vault(vault_app):
    """
    Simple setup function - call this in main.py before your integrations
    
    Usage in main.py:
        from vault_secure_integration import setup_secure_vault
        setup_secure_vault(self)  # Add this line
        
        # Then your existing integrations work:
        integrate_photo_vault(self)
        integrate_video_vault(self)
        integrate_recycle_bin(self)
    """
    print("🔒 Setting up secure vault storage...")
    
    # Initialize secure storage
    vault_app.secure_storage = SecureStorage("SecretVault")
    
    # Verify security
    security_check = vault_app.secure_storage.verify_security()
    if security_check['is_secure']:
        print("✅ Secure storage initialized successfully")
    else:
        print("⚠️ Security warnings:")
        for issue in security_check['issues']:
            print(f"  - {issue}")
    
    # Show storage location
    info = vault_app.secure_storage.get_storage_info()
    print(f"📁 Secure location: {info['base_directory']}")
    print(f"🛡️ Platform: {info['platform']}")
    
    return vault_app.secure_storage

def migrate_existing_files(vault_app):
    """
    Optional: Migrate existing files to secure storage
    Call this after setup_secure_vault() if you have existing files
    """
    if not hasattr(vault_app, 'secure_storage'):
        print("❌ Secure storage not initialized. Call setup_secure_vault() first.")
        return
    
    print("📦 Migrating existing files to secure storage...")
    migrated_count = 0
    
    # Migrate photos
    old_photo_dir = os.path.join(os.getcwd(), 'vault_photos')
    new_photo_dir = vault_app.secure_storage.get_vault_directory('photos')
    
    if os.path.exists(old_photo_dir) and old_photo_dir != new_photo_dir:
        migrated = migrate_folder(old_photo_dir, new_photo_dir, 
                                ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
        migrated_count += migrated
        print(f"📸 Migrated {migrated} photos")
    
    # Migrate videos
    old_video_dir = os.path.join(os.getcwd(), 'vault_videos')
    new_video_dir = vault_app.secure_storage.get_vault_directory('videos')
    
    if os.path.exists(old_video_dir) and old_video_dir != new_video_dir:
        migrated = migrate_folder(old_video_dir, new_video_dir, 
                                ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'])
        migrated_count += migrated
        print(f"🎬 Migrated {migrated} videos")
        
        # Migrate thumbnails
        old_thumb = os.path.join(old_video_dir, 'thumbnails')
        new_thumb = os.path.join(new_video_dir, 'thumbnails')
        if os.path.exists(old_thumb):
            if not os.path.exists(new_thumb):
                os.makedirs(new_thumb)
            thumb_migrated = migrate_folder(old_thumb, new_thumb, ['.jpg', '.jpeg', '.png'])
            print(f"🖼️ Migrated {thumb_migrated} thumbnails")
    
    # Migrate recycle bin
    old_recycle_dir = os.path.join(os.getcwd(), 'vault_recycle')
    new_recycle_dir = vault_app.secure_storage.get_recycle_directory()
    
    if os.path.exists(old_recycle_dir) and old_recycle_dir != new_recycle_dir:
        # Copy entire recycle structure
        try:
            if os.listdir(old_recycle_dir):  # If not empty
                for item in os.listdir(old_recycle_dir):
                    old_path = os.path.join(old_recycle_dir, item)
                    new_path = os.path.join(new_recycle_dir, item)
                    
                    if os.path.isfile(old_path):
                        shutil.move(old_path, new_path)
                        migrated_count += 1
                    elif os.path.isdir(old_path):
                        if not os.path.exists(new_path):
                            shutil.move(old_path, new_path)
                        else:
                            # Merge directories
                            sub_migrated = migrate_folder(old_path, new_path, [])
                            migrated_count += sub_migrated
                
                print(f"🗑️ Migrated recycle bin")
                
                # Remove old directory if empty
                try:
                    os.rmdir(old_recycle_dir)
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Error migrating recycle bin: {e}")
    
    print(f"✅ Migration complete: {migrated_count} files moved to secure storage")
    return migrated_count

def migrate_folder(source_dir, target_dir, extensions):
    """Helper function to migrate files from source to target"""
    migrated = 0
    
    try:
        for filename in os.listdir(source_dir):
            source_path = os.path.join(source_dir, filename)
            
            if os.path.isfile(source_path):
                # Check extension if specified
                if extensions and not any(filename.lower().endswith(ext) for ext in extensions):
                    continue
                
                target_path = os.path.join(target_dir, filename)
                
                # Handle filename conflicts
                counter = 1
                original_target = target_path
                while os.path.exists(target_path):
                    name, ext = os.path.splitext(original_target)
                    target_path = f"{name}_migrated_{counter}{ext}"
                    counter += 1
                
                shutil.move(source_path, target_path)
                migrated += 1
        
        # Remove source directory if empty
        try:
            if not os.listdir(source_dir):
                os.rmdir(source_dir)
        except:
            pass
            
    except Exception as e:
        print(f"Error migrating {source_dir}: {e}")
    
    return migrated

# Helper functions for vault modules to use
def get_secure_directory(vault_app, dir_type):
    """
    Get secure directory path for vault modules
    
    Args:
        vault_app: The main app instance
        dir_type: 'photos', 'videos', 'recycle', etc.
    """
    if hasattr(vault_app, 'secure_storage'):
        if dir_type == 'recycle':
            return vault_app.secure_storage.get_recycle_directory()
        else:
            return vault_app.secure_storage.get_vault_directory(dir_type)
    return None

def is_secure_storage_enabled(vault_app):
    """Check if secure storage is available"""
    return hasattr(vault_app, 'secure_storage') and vault_app.secure_storage is not None

# Simple all-in-one setup function
def initialize_secure_vault(vault_app, auto_migrate=True):
    """
    Complete setup - call this ONE time in main.py
    
    Usage:
        from vault_secure_integration import initialize_secure_vault
        initialize_secure_vault(self)  # Add this before your integrations
    """
    print("🚀 Initializing secure vault...")
    
    # Setup secure storage
    setup_secure_vault(vault_app)
    
    # Optional migration
    if auto_migrate:
        migrated = migrate_existing_files(vault_app)
        if migrated > 0:
            print(f"📦 Automatically migrated {migrated} existing files")
    
    print("✅ Secure vault ready! Your existing integrations will now use secure storage.")
    return vault_app.secure_storage

# For testing
if __name__ == "__main__":
    class MockApp:
        pass
    
    app = MockApp()
    initialize_secure_vault(app, auto_migrate=False)
    print("Test completed successfully!")