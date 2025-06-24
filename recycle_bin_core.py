import os
import json
import shutil
import threading
from datetime import datetime, timedelta
from kivy.clock import Clock

# Try to import Android-specific modules
try:
    from android.storage import app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

class RecycleBinCore:
    """
    Flexible Recycle Bin System for Secret Vault App
    
    Supports ANY file type: photos, videos, notes, audio, apps, documents, etc.
    Designed to be extensible for future vault additions.
    """
    
    # File type configurations - EASILY EXTENSIBLE
    FILE_TYPE_CONFIG = {
        'photos': {
            'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'retention_days': 30,
            'icon': '📷',
            'display_name': 'Photos'
        },
        'videos': {
            'extensions': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.ogg', '.ogv'],
            'retention_days': 7,  # Videos are large, shorter retention
            'icon': '🎬',
            'display_name': 'Videos'
        },
        'notes': {
            'extensions': ['.txt', '.md', '.note', '.json'],
            'retention_days': 60,  # Text files are small, longer retention
            'icon': '📝',
            'display_name': 'Notes'
        },
        'audio': {
            'extensions': ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'],
            'retention_days': 14,
            'icon': '🎵',
            'display_name': 'Audio'
        },
        'apps': {
            'extensions': ['.apk', '.exe', '.dmg', '.deb'],
            'retention_days': 90,  # Apps might be needed later
            'icon': '📱',
            'display_name': 'Apps'
        },
        'documents': {
            'extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
            'retention_days': 45,
            'icon': '📄',
            'display_name': 'Documents'
        },
        'other': {
            'extensions': [],  # Catch-all for unknown types
            'retention_days': 30,
            'icon': '📁',
            'display_name': 'Other Files'
        }
    }
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.recycle_dir = self.get_recycle_directory()
        self.metadata_file = os.path.join(self.recycle_dir, 'metadata.json')
        self.ensure_recycle_directory()
        self.metadata = self.load_metadata()
        
        # Start background cleanup task
        self.start_cleanup_scheduler()
    
    def get_recycle_directory(self):
        """Get the recycle bin directory"""
        if hasattr(self.app, 'secure_storage'):
            return self.app.secure_storage.get_recycle_directory()
        
        # Fallback to original
        if ANDROID:
            try:
                return os.path.join(app_storage_path(), 'vault_recycle')
            except:
                return os.path.join('/sdcard', 'vault_recycle')
        else:
            return os.path.join(os.getcwd(), 'vault_recycle')
    
    def ensure_recycle_directory(self):
        """Create recycle directory structure for all file types"""
        try:
            if not os.path.exists(self.recycle_dir):
                os.makedirs(self.recycle_dir)
            
            # Create subdirectories for each file type
            for file_type in self.FILE_TYPE_CONFIG.keys():
                type_dir = os.path.join(self.recycle_dir, file_type)
                if not os.path.exists(type_dir):
                    os.makedirs(type_dir)
                    
        except Exception as e:
            print(f"Error creating recycle directory: {e}")
    
    def detect_file_type(self, file_path):
        """Detect file type based on extension - EXTENSIBLE"""
        if not os.path.exists(file_path):
            return 'other'
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        for file_type, config in self.FILE_TYPE_CONFIG.items():
            if file_ext in config['extensions']:
                return file_type
        
        return 'other'  # Unknown file types go to 'other'
    
    def generate_recycled_filename(self, original_path, file_type):
        """Generate unique filename for recycled file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        original_name = os.path.basename(original_path)
        
        # Format: deleted_TIMESTAMP_originalname.ext
        name_part, ext_part = os.path.splitext(original_name)
        recycled_name = f"deleted_{timestamp}_{name_part}{ext_part}"
        
        return os.path.join(self.recycle_dir, file_type, recycled_name)
    
    def move_to_recycle(self, file_path, original_location=None, metadata=None):
        """
        Move file to recycle bin - MAIN FUNCTION
        
        Args:
            file_path: Path to file to be recycled
            original_location: Original location (for restoration)
            metadata: Additional metadata dict (thumbnails, notes, etc.)
        
        Returns:
            dict: Success status and recycled file info
        """
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            # Detect file type
            file_type = self.detect_file_type(file_path)
            
            # Generate recycled filename
            recycled_path = self.generate_recycled_filename(file_path, file_type)
            
            # Move file to recycle bin
            shutil.move(file_path, recycled_path)
            
            # Store metadata
            recycled_info = {
                'original_path': file_path,
                'original_location': original_location or os.path.dirname(file_path),
                'recycled_path': recycled_path,
                'file_type': file_type,
                'deleted_at': datetime.now().isoformat(),
                'size': os.path.getsize(recycled_path),
                'metadata': metadata or {}
            }
            
            # Add to metadata tracking
            recycled_id = os.path.basename(recycled_path)
            self.metadata[recycled_id] = recycled_info
            self.save_metadata()
            
            print(f"✅ File recycled: {file_path} -> {recycled_path}")
            
            # Handle associated files (thumbnails, etc.)
            self.handle_associated_files(file_path, recycled_path, file_type)
            
            return {
                'success': True,
                'recycled_path': recycled_path,
                'file_type': file_type,
                'recycled_info': recycled_info
            }
            
        except Exception as e:
            print(f"❌ Error moving to recycle: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_associated_files(self, original_path, recycled_path, file_type):
        """Handle associated files like thumbnails - EXTENSIBLE"""
        try:
            # Handle video thumbnails
            if file_type == 'videos':
                # Move thumbnail if it exists
                vault_dir = os.path.dirname(os.path.dirname(original_path))  # Go up from vault_videos
                thumb_dir = os.path.join(vault_dir, 'vault_videos', 'thumbnails')
                
                if os.path.exists(thumb_dir):
                    filename = os.path.splitext(os.path.basename(original_path))[0]
                    thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
                    
                    if os.path.exists(thumb_path):
                        # Move thumbnail to recycle bin
                        recycled_thumb_dir = os.path.join(self.recycle_dir, 'thumbnails')
                        if not os.path.exists(recycled_thumb_dir):
                            os.makedirs(recycled_thumb_dir)
                        
                        recycled_thumb_name = f"deleted_{os.path.basename(recycled_path)}_thumb.jpg"
                        recycled_thumb_path = os.path.join(recycled_thumb_dir, recycled_thumb_name)
                        
                        shutil.move(thumb_path, recycled_thumb_path)
                        print(f"✅ Thumbnail recycled: {thumb_path} -> {recycled_thumb_path}")
            
            # Future: Handle other associated files
            # elif file_type == 'notes':
            #     # Handle note attachments, backups, etc.
            # elif file_type == 'audio':
            #     # Handle album art, playlists, etc.
            
        except Exception as e:
            print(f"⚠️ Warning: Could not handle associated files: {e}")
    
    def restore_from_recycle(self, recycled_id, restore_location=None):
        """
        Restore file from recycle bin
        
        Args:
            recycled_id: ID of recycled file (filename in recycle bin)
            restore_location: Custom restore location (optional)
        
        Returns:
            dict: Success status and restored file info
        """
        try:
            if recycled_id not in self.metadata:
                return {'success': False, 'error': 'File not found in recycle bin'}
            
            recycled_info = self.metadata[recycled_id]
            recycled_path = recycled_info['recycled_path']
            
            if not os.path.exists(recycled_path):
                return {'success': False, 'error': 'Recycled file missing from disk'}
            
            # Determine restore location
            if restore_location:
                restored_path = restore_location
            else:
                # Restore to original location or vault
                original_location = recycled_info['original_location']
                original_filename = os.path.basename(recycled_info['original_path'])
                restored_path = os.path.join(original_location, original_filename)
            
            # Handle filename conflicts
            restored_path = self.resolve_restore_conflicts(restored_path)
            
            # Move file back
            shutil.move(recycled_path, restored_path)
            
            # Restore associated files
            self.restore_associated_files(recycled_info, restored_path)
            
            # Remove from metadata
            del self.metadata[recycled_id]
            self.save_metadata()
            
            print(f"✅ File restored: {recycled_path} -> {restored_path}")
            
            return {
                'success': True,
                'restored_path': restored_path,
                'original_info': recycled_info
            }
            
        except Exception as e:
            print(f"❌ Error restoring file: {e}")
            return {'success': False, 'error': str(e)}
    
    def resolve_restore_conflicts(self, target_path):
        """Handle filename conflicts during restore"""
        if not os.path.exists(target_path):
            return target_path
        
        # Add (Restored) suffix
        name_part, ext_part = os.path.splitext(target_path)
        counter = 1
        
        while True:
            new_path = f"{name_part} (Restored {counter}){ext_part}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    def restore_associated_files(self, recycled_info, restored_path):
        """Restore associated files like thumbnails"""
        try:
            file_type = recycled_info['file_type']
            
            if file_type == 'videos':
                # Restore thumbnail
                recycled_thumb_dir = os.path.join(self.recycle_dir, 'thumbnails')
                recycled_basename = os.path.basename(recycled_info['recycled_path'])
                thumb_name = f"deleted_{recycled_basename}_thumb.jpg"
                recycled_thumb_path = os.path.join(recycled_thumb_dir, thumb_name)
                
                if os.path.exists(recycled_thumb_path):
                    # Restore to vault thumbnails directory
                    vault_dir = os.path.dirname(os.path.dirname(restored_path))
                    thumb_dir = os.path.join(vault_dir, 'thumbnails')
                    
                    if not os.path.exists(thumb_dir):
                        os.makedirs(thumb_dir)
                    
                    filename = os.path.splitext(os.path.basename(restored_path))[0]
                    restored_thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
                    
                    shutil.move(recycled_thumb_path, restored_thumb_path)
                    print(f"✅ Thumbnail restored: {recycled_thumb_path} -> {restored_thumb_path}")
        
        except Exception as e:
            print(f"⚠️ Warning: Could not restore associated files: {e}")
    
    def delete_permanently(self, recycled_id):
        """Permanently delete file from recycle bin"""
        try:
            if recycled_id not in self.metadata:
                return {'success': False, 'error': 'File not found in recycle bin'}
            
            recycled_info = self.metadata[recycled_id]
            recycled_path = recycled_info['recycled_path']
            
            # Delete file
            if os.path.exists(recycled_path):
                os.remove(recycled_path)
            
            # Delete associated files
            self.delete_associated_files_permanently(recycled_info)
            
            # Remove from metadata
            del self.metadata[recycled_id]
            self.save_metadata()
            
            print(f"✅ File permanently deleted: {recycled_path}")
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Error permanently deleting file: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_associated_files_permanently(self, recycled_info):
        """Permanently delete associated files"""
        try:
            file_type = recycled_info['file_type']
            
            if file_type == 'videos':
                # Delete thumbnail
                recycled_thumb_dir = os.path.join(self.recycle_dir, 'thumbnails')
                recycled_basename = os.path.basename(recycled_info['recycled_path'])
                thumb_name = f"deleted_{recycled_basename}_thumb.jpg"
                recycled_thumb_path = os.path.join(recycled_thumb_dir, thumb_name)
                
                if os.path.exists(recycled_thumb_path):
                    os.remove(recycled_thumb_path)
                    print(f"✅ Thumbnail permanently deleted: {recycled_thumb_path}")
        
        except Exception as e:
            print(f"⚠️ Warning: Could not delete associated files: {e}")
    
    def cleanup_expired_files(self):
        """Clean up files that have exceeded their retention period"""
        try:
            current_time = datetime.now()
            expired_files = []
            
            for recycled_id, info in self.metadata.items():
                deleted_at = datetime.fromisoformat(info['deleted_at'])
                file_type = info['file_type']
                retention_days = self.FILE_TYPE_CONFIG[file_type]['retention_days']
                
                if current_time - deleted_at > timedelta(days=retention_days):
                    expired_files.append(recycled_id)
            
            # Delete expired files
            for recycled_id in expired_files:
                result = self.delete_permanently(recycled_id)
                if result['success']:
                    print(f"🧹 Auto-deleted expired file: {recycled_id}")
            
            return len(expired_files)
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return 0
    
    def get_recycled_files(self, file_type=None):
        """Get list of recycled files, optionally filtered by type"""
        try:
            files = []
            
            for recycled_id, info in self.metadata.items():
                if file_type is None or info['file_type'] == file_type:
                    # Add additional info for UI
                    info_copy = info.copy()
                    info_copy['recycled_id'] = recycled_id
                    info_copy['display_name'] = os.path.basename(info['original_path'])
                    info_copy['days_remaining'] = self.get_days_remaining(info)
                    files.append(info_copy)
            
            # Sort by deletion date (newest first)
            files.sort(key=lambda x: x['deleted_at'], reverse=True)
            return files
            
        except Exception as e:
            print(f"❌ Error getting recycled files: {e}")
            return []
    
    def get_days_remaining(self, recycled_info):
        """Get days remaining before permanent deletion"""
        try:
            deleted_at = datetime.fromisoformat(recycled_info['deleted_at'])
            file_type = recycled_info['file_type']
            retention_days = self.FILE_TYPE_CONFIG[file_type]['retention_days']
            
            expiry_date = deleted_at + timedelta(days=retention_days)
            days_remaining = (expiry_date - datetime.now()).days
            
            return max(0, days_remaining)
            
        except Exception as e:
            print(f"Error calculating days remaining: {e}")
            return 0
    
    def get_recycle_bin_stats(self):
        """Get recycle bin statistics"""
        try:
            stats = {
                'total_files': 0,
                'total_size_mb': 0,
                'by_type': {}
            }
            
            for file_type in self.FILE_TYPE_CONFIG.keys():
                stats['by_type'][file_type] = {
                    'count': 0,
                    'size_mb': 0,
                    'icon': self.FILE_TYPE_CONFIG[file_type]['icon'],
                    'display_name': self.FILE_TYPE_CONFIG[file_type]['display_name']
                }
            
            for info in self.metadata.values():
                file_type = info['file_type']
                file_size = info.get('size', 0)
                
                stats['total_files'] += 1
                stats['total_size_mb'] += file_size / (1024 * 1024)
                
                stats['by_type'][file_type]['count'] += 1
                stats['by_type'][file_type]['size_mb'] += file_size / (1024 * 1024)
            
            # Round sizes
            stats['total_size_mb'] = round(stats['total_size_mb'], 1)
            for file_type in stats['by_type']:
                stats['by_type'][file_type]['size_mb'] = round(stats['by_type'][file_type]['size_mb'], 1)
            
            return stats
            
        except Exception as e:
            print(f"Error getting recycle bin stats: {e}")
            return {'total_files': 0, 'total_size_mb': 0, 'by_type': {}}
    
    def empty_recycle_bin(self, file_type=None):
        """Empty recycle bin (all files or specific type)"""
        try:
            deleted_count = 0
            files_to_delete = []
            
            for recycled_id, info in self.metadata.items():
                if file_type is None or info['file_type'] == file_type:
                    files_to_delete.append(recycled_id)
            
            for recycled_id in files_to_delete:
                result = self.delete_permanently(recycled_id)
                if result['success']:
                    deleted_count += 1
            
            return {'success': True, 'deleted_count': deleted_count}
            
        except Exception as e:
            print(f"❌ Error emptying recycle bin: {e}")
            return {'success': False, 'error': str(e), 'deleted_count': 0}
    
    def load_metadata(self):
        """Load metadata from JSON file"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}
    
    def save_metadata(self):
        """Save metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def start_cleanup_scheduler(self):
        """Start background cleanup scheduler"""
        def cleanup_worker():
            try:
                expired_count = self.cleanup_expired_files()
                if expired_count > 0:
                    print(f"🧹 Cleanup completed: {expired_count} expired files deleted")
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
        
        # Schedule cleanup every 24 hours
        def schedule_cleanup():
            cleanup_worker()
            Clock.schedule_once(lambda dt: schedule_cleanup(), 86400)  # 24 hours
        
        # Initial cleanup and start scheduler
        Clock.schedule_once(lambda dt: schedule_cleanup(), 5)  # Start after 5 seconds

# FUTURE EXTENSIBILITY EXAMPLES:

def add_new_file_type(file_type_name, extensions, retention_days, icon, display_name):
    """
    Helper function to add new file types dynamically
    
    Example usage:
    add_new_file_type('scripts', ['.py', '.js', '.sh'], 45, '🐍', 'Scripts')
    add_new_file_type('archives', ['.zip', '.rar', '.7z'], 60, '📦', 'Archives')
    """
    RecycleBinCore.FILE_TYPE_CONFIG[file_type_name] = {
        'extensions': extensions,
        'retention_days': retention_days,
        'icon': icon,
        'display_name': display_name
    }

print(f"📁 Supports {len(RecycleBinCore.FILE_TYPE_CONFIG)} file types out of the box")