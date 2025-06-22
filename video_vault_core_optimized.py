import os
import shutil
import threading
import subprocess
import platform
import gc
import time
import re
import json
import signal
import weakref
from datetime import datetime
from kivy.clock import Clock
from PIL import Image as PILImage

# Try to import Android-specific modules
try:
    from android.permissions import request_permissions, Permission
    from plyer import filechooser
    from android.storage import primary_external_storage_path, app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False
    import tkinter as tk
    from tkinter import filedialog

# Try to import video processing libraries
try:
    import imageio
    import imageio_ffmpeg
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    print("ImageIO not available - video thumbnails will use basic method")

# Windows-specific imports for advanced file operations
if platform.system() == "Windows":
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
        print("psutil not available - advanced file deletion disabled")

class ResourceManager:
    """Centralized resource management to prevent memory leaks"""
    
    def __init__(self):
        # Use WeakSet to automatically remove dead references
        self.imageio_readers = weakref.WeakSet()
        self.video_players = weakref.WeakSet()
        self.temp_files = set()
        self.background_threads = weakref.WeakSet()
        self.cleanup_scheduled = False
    
    def register_imageio_reader(self, reader):
        """Register ImageIO reader for cleanup"""
        if reader:
            self.imageio_readers.add(reader)
    
    def register_video_player(self, player):
        """Register video player for cleanup"""
        if player:
            self.video_players.add(player)
    
    def register_temp_file(self, file_path):
        """Register temporary file for cleanup"""
        if file_path:
            self.temp_files.add(file_path)
    
    def register_thread(self, thread):
        """Register background thread for tracking"""
        if thread:
            self.background_threads.add(thread)
    
    def cleanup_imageio_readers(self):
        """Clean up all ImageIO readers"""
        cleaned = 0
        try:
            # Create a copy to avoid modification during iteration
            readers_copy = list(self.imageio_readers)
            
            for reader in readers_copy:
                try:
                    if reader and hasattr(reader, 'close'):
                        reader.close()
                        cleaned += 1
                except Exception as e:
                    print(f"Error closing ImageIO reader: {e}")
            
            # Clear the set
            self.imageio_readers.clear()
            
            if cleaned > 0:
                print(f"✅ Cleaned up {cleaned} ImageIO readers")
                
        except Exception as e:
            print(f"Error in ImageIO cleanup: {e}")
        
        return cleaned
    
    def cleanup_video_players(self):
        """Clean up all video players"""
        cleaned = 0
        try:
            players_copy = list(self.video_players)
            
            for player in players_copy:
                try:
                    if player:
                        if hasattr(player, 'state'):
                            player.state = 'stop'
                        if hasattr(player, 'unload'):
                            player.unload()
                        if hasattr(player, 'texture'):
                            player.texture = None
                        cleaned += 1
                except Exception as e:
                    print(f"Error cleaning video player: {e}")
            
            self.video_players.clear()
            
            if cleaned > 0:
                print(f"✅ Cleaned up {cleaned} video players")
                
        except Exception as e:
            print(f"Error in video player cleanup: {e}")
        
        return cleaned
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        cleaned = 0
        temp_files_copy = self.temp_files.copy()
        
        for file_path in temp_files_copy:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned += 1
                self.temp_files.discard(file_path)
            except Exception as e:
                print(f"Error removing temp file {file_path}: {e}")
        
        if cleaned > 0:
            print(f"✅ Cleaned up {cleaned} temp files")
        
        return cleaned
    
    def full_cleanup(self):
        """Perform complete resource cleanup"""
        print("🧹 Starting full resource cleanup...")
        
        total_cleaned = 0
        total_cleaned += self.cleanup_imageio_readers()
        total_cleaned += self.cleanup_video_players()
        total_cleaned += self.cleanup_temp_files()
        
        # Force garbage collection
        collected = gc.collect()
        
        print(f"✅ Full cleanup complete: {total_cleaned} resources, {collected} objects collected")
        return total_cleaned
    
    def schedule_periodic_cleanup(self):
        """Schedule periodic cleanup to prevent memory buildup"""
        if not self.cleanup_scheduled:
            self.cleanup_scheduled = True
            Clock.schedule_interval(self.periodic_cleanup, 30)  # Every 30 seconds
    
    def periodic_cleanup(self, dt):
        """Periodic cleanup callback"""
        try:
            # Only cleanup if we have significant resources
            reader_count = len(self.imageio_readers)
            player_count = len(self.video_players)
            temp_count = len(self.temp_files)
            
            if reader_count > 5 or player_count > 3 or temp_count > 10:
                print(f"🧹 Periodic cleanup: {reader_count} readers, {player_count} players, {temp_count} temp files")
                self.full_cleanup()
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")

class VideoVaultCore:
    """Core video vault functionality with proper resource management"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.vault_dir = self.get_vault_directory()
        self.ensure_vault_directory()
        self.processing = False
        
        # NEW: Centralized resource management
        self.resource_manager = ResourceManager()
        self.resource_manager.schedule_periodic_cleanup()
        
        # NEW: Video info cache to avoid repeated file operations
        self.video_info_cache = {}
        self.video_info_cache_file = os.path.join(self.vault_dir, 'video_info_cache.json')
        self.load_video_info_cache()
        
        # Track widget references for cleanup
        self.widget_references = weakref.WeakSet()
    
    def register_widget(self, widget):
        """Register widget for memory management"""
        if widget:
            self.widget_references.add(widget)
    
    def cleanup_widgets(self):
        """Clean up registered widgets"""
        cleaned = 0
        widgets_copy = list(self.widget_references)
        
        for widget in widgets_copy:
            try:
                if widget and hasattr(widget, 'clear_widgets'):
                    widget.clear_widgets()
                if hasattr(widget, 'texture'):
                    widget.texture = None
                if hasattr(widget, 'source'):
                    widget.source = ''
                cleaned += 1
            except Exception as e:
                print(f"Error cleaning widget: {e}")
        
        self.widget_references.clear()
        
        if cleaned > 0:
            print(f"✅ Cleaned up {cleaned} widgets")
        
        return cleaned
    
    def get_vault_directory(self):
        """Get the secure directory for storing vault videos"""
        if hasattr(self.app, 'secure_storage'):
            return self.app.secure_storage.get_vault_directory('videos')
        
        # Fallback to original
        if ANDROID:
            try:
                return os.path.join(app_storage_path(), 'vault_videos')
            except:
                return os.path.join('/sdcard', 'vault_videos')
        else:
            return os.path.join(os.getcwd(), 'vault_videos')
    
    def ensure_vault_directory(self):
        """Create vault directory if it doesn't exist"""
        try:
            if not os.path.exists(self.vault_dir):
                os.makedirs(self.vault_dir)
            # Also create thumbnails subdirectory
            thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
        except Exception as e:
            print(f"Error creating vault directory: {e}")
    
    def request_permissions(self):
        """Request necessary permissions for file access"""
        if ANDROID:
            try:
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.CAMERA  # For video access
                ])
            except Exception as e:
                print(f"Permission error: {e}")
    
    def load_video_info_cache(self):
        """Load video info cache from disk"""
        try:
            if os.path.exists(self.video_info_cache_file):
                with open(self.video_info_cache_file, 'r') as f:
                    self.video_info_cache = json.load(f)
                print(f"✅ Loaded video info cache: {len(self.video_info_cache)} entries")
            else:
                self.video_info_cache = {}
        except Exception as e:
            print(f"Error loading video info cache: {e}")
            self.video_info_cache = {}

    def save_video_info_cache(self):
        """Save video info cache to disk"""
        try:
            with open(self.video_info_cache_file, 'w') as f:
                json.dump(self.video_info_cache, f, indent=2)
        except Exception as e:
            print(f"Error saving video info cache: {e}")
    
    def is_valid_video(self, file_path):
        """Check if file is a valid video"""
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.ogg', '.ogv']
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    def generate_thumbnail_safe(self, video_path):
        """Generate thumbnail for video with proper caching and resource management"""
        try:
            thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
            filename = os.path.splitext(os.path.basename(video_path))[0]
            thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
            
            # CRITICAL FIX 1: Check if thumbnail already exists
            if os.path.exists(thumb_path):
                print(f"✅ Thumbnail already exists: {thumb_path}")
                return thumb_path
            
            print(f"🔄 Generating new thumbnail for: {video_path}")
            
            if IMAGEIO_AVAILABLE:
                reader = None
                try:
                    # Create ImageIO reader object
                    reader = imageio.get_reader(video_path, 'ffmpeg')
                    self.resource_manager.register_imageio_reader(reader)
                    
                    # Get the first frame
                    frame = reader.get_data(0)
                    
                    if frame is not None:
                        # Convert numpy array to PIL Image
                        pil_image = PILImage.fromarray(frame)
                        
                        # OPTIMIZATION: Use smaller thumbnail size for faster processing
                        width, height = pil_image.size
                        aspect_ratio = width / height
                        
                        # Reduced size: 150x150 instead of 200x200 for faster generation
                        if aspect_ratio > 1:  # Landscape
                            new_width = 150
                            new_height = int(150 / aspect_ratio)
                        else:  # Portrait
                            new_height = 150
                            new_width = int(150 * aspect_ratio)
                        
                        # Use faster resampling method
                        thumbnail = pil_image.resize((new_width, new_height), PILImage.Resampling.BILINEAR)
                        
                        # OPTIMIZATION: Use lower quality JPEG for smaller files and faster saving
                        thumbnail.save(thumb_path, 'JPEG', quality=75, optimize=True)
                        print(f"✅ Thumbnail generated: {thumb_path}")
                    
                    # CRITICAL: Immediate cleanup
                    if reader is not None:
                        reader.close()
                        reader = None
                    
                except Exception as e:
                    print(f"ImageIO thumbnail generation error: {e}")
                    # Create placeholder instead of failing
                    self.generate_placeholder_thumbnail(thumb_path)
                finally:
                    # Ensure cleanup
                    if reader is not None:
                        try:
                            reader.close()
                        except:
                            pass
            else:
                # Fallback: create placeholder
                self.generate_placeholder_thumbnail(thumb_path)
            
            return thumb_path
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None
    
    def generate_placeholder_thumbnail(self, thumb_path):
        """Generate a lightweight placeholder thumbnail"""
        try:
            # Create smaller placeholder for faster generation
            img = PILImage.new('RGB', (150, 110), color='#37474F')  # BlueGray color
            
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Use default font only - no font file loading
                font = ImageFont.load_default()
                
                # Simple text
                text = "VIDEO"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                position = ((150 - text_width) // 2, (110 - text_height) // 2)
                draw.text(position, text, fill='white', font=font)
                
            except ImportError:
                # PIL doesn't have text drawing - just use solid color
                pass
            
            # Save with lower quality for speed
            img.save(thumb_path, 'JPEG', quality=60, optimize=True)
            print(f"✅ Placeholder thumbnail created: {thumb_path}")
        except Exception as e:
            print(f"Error generating placeholder thumbnail: {e}")
    
    def get_thumbnail_path(self, video_path):
        """Get thumbnail path for a video - OPTIMIZED VERSION"""
        thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
        filename = os.path.splitext(os.path.basename(video_path))[0]
        thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
        
        # CRITICAL FIX: Only return existing thumbnails, don't generate here
        if os.path.exists(thumb_path):
            return thumb_path
        else:
            # Return None instead of generating - let UI handle missing thumbnails gracefully
            return None
    
    def generate_thumbnails_background(self, video_paths, callback=None):
        """Generate thumbnails in background thread"""
        def thumbnail_worker():
            generated_count = 0
            for video_path in video_paths:
                try:
                    if self.generate_thumbnail_safe(video_path):
                        generated_count += 1
                        # Update UI every few thumbnails
                        if generated_count % 3 == 0 and callback:
                            Clock.schedule_once(lambda dt: callback(), 0)
                except Exception as e:
                    print(f"Background thumbnail error for {video_path}: {e}")
            
            print(f"✅ Background thumbnail generation complete: {generated_count}/{len(video_paths)}")
            if callback:
                Clock.schedule_once(lambda dt: callback(), 0)
        
        # Start background thread
        thread = threading.Thread(target=thumbnail_worker)
        thread.daemon = True
        self.resource_manager.register_thread(thread)
        thread.start()

print("✅ Video Vault Core Optimized loaded successfully")
print("🧹 Memory leak fixes: ResourceManager, WeakRefs, proper cleanup")
print("📋 Performance optimizations: Caching, background processing")