# vault_secure_integration.py - Optimized connector between secure_storage.py and vault modules
"""
✅ OPTIMIZED VERSION with better performance and memory management
Much simpler than the original complex version with added optimizations.
"""

from secure_storage import SecureStorage
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# ✅ OPTIMIZATION: Global thread pool for file operations
_file_operation_pool = None
_pool_lock = threading.Lock()

def get_file_operation_pool():
    """✅ OPTIMIZATION: Lazy thread pool creation"""
    global _file_operation_pool
    if _file_operation_pool is None:
        with _pool_lock:
            if _file_operation_pool is None:
                _file_operation_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="FileOp")
    return _file_operation_pool

def setup_secure_vault(vault_app):
    """
    ✅ OPTIMIZED: Simple setup function with performance improvements
    
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
    
    # ✅ OPTIMIZATION: Quick security check without full verification
    is_secure_location = not vault_app.secure_storage.is_user_accessible()
    
    if is_secure_location:
        print("✅ Secure storage initialized successfully")
    else:
        print("⚠️ Warning: Storage location may be user-accessible")
    
    # Show storage location
    print(f"📁 Secure location: {vault_app.secure_storage.base_dir}")
    print(f"🛡️ Platform: {vault_app.secure_storage.get_platform_name()}")
    
    return vault_app.secure_storage

def migrate_existing_files_async(vault_app):
    """
    ✅ OPTIMIZATION: Asynchronous file migration for better performance
    Call this after setup_secure_vault() if you have existing files
    """
    if not hasattr(vault_app, 'secure_storage'):
        print("❌ Secure storage not initialized. Call setup_secure_vault() first.")
        return
    
    print("📦 Starting async migration of existing files...")
    
    # Submit migration task to thread pool
    future = get_file_operation_pool().submit(_migrate_files_worker, vault_app)
    
    # Return future for tracking if needed
    return future

def _migrate_files_worker(vault_app):
    """✅ OPTIMIZATION: Worker function for async migration"""
    try:
        migrated_count = 0
        start_time = time.time()
        
        # ✅ OPTIMIZATION: Batch migration operations
        migration_tasks = [
            {
                'old_dir': os.path.join(os.getcwd(), 'vault_photos'),
                'new_dir': vault_app.secure_storage.get_vault_directory('photos'),
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
                'name': 'photos'
            },
            {
                'old_dir': os.path.join(os.getcwd(), 'vault_videos'),
                'new_dir': vault_app.secure_storage.get_vault_directory('videos'),
                'extensions': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
                'name': 'videos'
            },
            {
                'old_dir': os.path.join(os.getcwd(), 'vault_recycle'),
                'new_dir': vault_app.secure_storage.get_recycle_directory(),
                'extensions': [],  # All files
                'name': 'recycle bin'
            }
        ]
        
        for task in migration_tasks:
            if os.path.exists(task['old_dir']) and task['old_dir'] != task['new_dir']:
                migrated = _migrate_folder_optimized(
                    task['old_dir'], 
                    task['new_dir'], 
                    task['extensions']
                )
                migrated_count += migrated
                if migrated > 0:
                    print(f"📦 Migrated {migrated} {task['name']}")
        
        # Handle video thumbnails separately
        old_video_dir = os.path.join(os.getcwd(), 'vault_videos')
        if os.path.exists(old_video_dir):
            old_thumb = os.path.join(old_video_dir, 'thumbnails')
            new_thumb = os.path.join(vault_app.secure_storage.get_vault_directory('videos'), 'thumbnails')
            if os.path.exists(old_thumb):
                if not os.path.exists(new_thumb):
                    os.makedirs(new_thumb)
                thumb_migrated = _migrate_folder_optimized(old_thumb, new_thumb, ['.jpg', '.jpeg', '.png'])
                if thumb_migrated > 0:
                    print(f"🖼️ Migrated {thumb_migrated} thumbnails")
                    migrated_count += thumb_migrated
        
        elapsed_time = time.time() - start_time
        print(f"✅ Migration complete: {migrated_count} files moved in {elapsed_time:.2f}s")
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error during async migration: {e}")
        return 0

def migrate_existing_files(vault_app):
    """
    ✅ OPTIMIZATION: Synchronous version with performance improvements
    Call this after setup_secure_vault() if you have existing files
    """
    if not hasattr(vault_app, 'secure_storage'):
        print("❌ Secure storage not initialized. Call setup_secure_vault() first.")
        return
    
    print("📦 Migrating existing files to secure storage...")
    
    # Use the worker function directly for sync operation
    return _migrate_files_worker(vault_app)

def _migrate_folder_optimized(source_dir, target_dir, extensions):
    """✅ OPTIMIZATION: Faster folder migration with batch operations"""
    migrated = 0
    
    try:
        # ✅ OPTIMIZATION: Use pathlib for better performance
        source_path = Path(source_dir)
        target_path = Path(target_dir)
        
        if not source_path.exists():
            return 0
        
        # Ensure target directory exists
        target_path.mkdir(parents=True, exist_ok=True)
        
        # ✅ OPTIMIZATION: Use os.scandir for faster directory scanning
        files_to_move = []
        
        for entry in os.scandir(source_dir):
            if entry.is_file():
                # Check extension if specified
                if extensions and not any(entry.name.lower().endswith(ext) for ext in extensions):
                    continue
                files_to_move.append(entry.path)
            elif entry.is_dir() and not extensions:
                # For directories (like recycle bin), handle recursively
                sub_migrated = _migrate_folder_optimized(
                    entry.path, 
                    os.path.join(target_dir, entry.name), 
                    extensions
                )
                migrated += sub_migrated
        
        # ✅ OPTIMIZATION: Batch file moves
        for source_file in files_to_move:
            filename = os.path.basename(source_file)
            target_file = os.path.join(target_dir, filename)
            
            # Handle filename conflicts efficiently
            if os.path.exists(target_file):
                target_file = _get_unique_filename(target_file)
            
            try:
                shutil.move(source_file, target_file)
                migrated += 1
            except Exception as e:
                print(f"⚠️ Failed to move {source_file}: {e}")
        
        # ✅ OPTIMIZATION: Clean up empty source directory
        try:
            if source_path.exists() and not any(source_path.iterdir()):
                source_path.rmdir()
        except:
            pass  # Directory not empty or other issue
            
    except Exception as e:
        print(f"❌ Error migrating {source_dir}: {e}")
    
    return migrated

def _get_unique_filename(target_path):
    """✅ OPTIMIZATION: Faster unique filename generation"""
    path_obj = Path(target_path)
    counter = 1
    
    while path_obj.exists():
        new_name = f"{path_obj.stem}_migrated_{counter}{path_obj.suffix}"
        path_obj = path_obj.parent / new_name
        counter += 1
    
    return str(path_obj)

# ✅ OPTIMIZATION: Cached helper functions
_directory_cache = {}
_cache_lock_dirs = threading.Lock()

def get_secure_directory(vault_app, dir_type):
    """
    ✅ OPTIMIZATION: Cached directory lookup for vault modules
    
    Args:
        vault_app: The main app instance
        dir_type: 'photos', 'videos', 'recycle', etc.
    """
    if not hasattr(vault_app, 'secure_storage'):
        return None
    
    # Check cache first
    cache_key = (id(vault_app.secure_storage), dir_type)
    
    with _cache_lock_dirs:
        if cache_key in _directory_cache:
            return _directory_cache[cache_key]
    
    # Calculate and cache
    if dir_type == 'recycle':
        directory = vault_app.secure_storage.get_recycle_directory()
    else:
        directory = vault_app.secure_storage.get_vault_directory(dir_type)
    
    with _cache_lock_dirs:
        _directory_cache[cache_key] = directory
    
    return directory

def is_secure_storage_enabled(vault_app):
    """Check if secure storage is available"""
    return hasattr(vault_app, 'secure_storage') and vault_app.secure_storage is not None

def clear_directory_cache():
    """✅ OPTIMIZATION: Clear directory cache"""
    with _cache_lock_dirs:
        _directory_cache.clear()
    print("🧹 Directory cache cleared")

# ✅ OPTIMIZATION: All-in-one setup with performance monitoring
def initialize_secure_vault(vault_app, auto_migrate=True, async_migrate=False):
    """
    ✅ OPTIMIZED: Complete setup with performance monitoring
    
    Usage:
        from vault_secure_integration import initialize_secure_vault
        initialize_secure_vault(self)  # Add this before your integrations
    
    Args:
        vault_app: The main app instance
        auto_migrate: Whether to migrate existing files automatically
        async_migrate: Whether to use async migration (recommended for large files)
    """
    print("🚀 Initializing secure vault...")
    start_time = time.time()
    
    # Setup secure storage
    setup_secure_vault(vault_app)
    
    # Optional migration
    migration_future = None
    if auto_migrate:
        if async_migrate:
            migration_future = migrate_existing_files_async(vault_app)
            print("📦 Started async migration in background")
        else:
            migrated = migrate_existing_files(vault_app)
            if migrated > 0:
                print(f"📦 Migrated {migrated} existing files")
    
    elapsed_time = time.time() - start_time
    print(f"✅ Secure vault ready in {elapsed_time:.2f}s! Your existing integrations will now use secure storage.")
    
    # Return both storage and migration future for tracking
    return vault_app.secure_storage, migration_future

def cleanup_vault_integration():
    """✅ OPTIMIZATION: Cleanup function for app shutdown"""
    global _file_operation_pool
    
    clear_directory_cache()
    
    if _file_operation_pool:
        _file_operation_pool.shutdown(wait=False)
        _file_operation_pool = None
    
    print("🧹 Vault integration cleanup completed")

# ✅ OPTIMIZATION: Performance monitoring
def get_vault_performance_stats(vault_app):
    """Get performance statistics for debugging"""
    if not hasattr(vault_app, 'secure_storage'):
        return {"error": "Secure storage not initialized"}
    
    stats = {
        "storage_info": vault_app.secure_storage.get_storage_info(),
        "cache_stats": vault_app.secure_storage.get_cache_stats(),
        "directory_cache_size": len(_directory_cache),
        "thread_pool_active": _file_operation_pool is not None
    }
    
    return stats

# For testing
if __name__ == "__main__":
    class MockApp:
        pass
    
    app = MockApp()
    storage, migration_future = initialize_secure_vault(app, auto_migrate=False, async_migrate=True)
    
    # Show performance stats
    stats = get_vault_performance_stats(app)
    print(f"📊 Performance Stats: {stats}")
    
    print("✅ Test completed successfully!")
    
    # Cleanup
    cleanup_vault_integration()