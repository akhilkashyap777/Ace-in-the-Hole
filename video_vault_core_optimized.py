import os
import threading
import platform
import gc
import json
import weakref
from kivy.clock import Clock
from PIL import Image as PILImage

# REMOVED: Android imports completely
# No more android.permissions, plyer, android.storage
ANDROID = False  # Always False for desktop-only version

try:
    import imageio
    import imageio_ffmpeg
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    print("ImageIO not available - video thumbnails will use basic method")

if platform.system() == "Windows":
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
        print("psutil not available - advanced file deletion disabled")

class ResourceManager:
    def __init__(self):
        self.imageio_readers = weakref.WeakSet()
        self.video_players = weakref.WeakSet()
        self.temp_files = set()
        self.background_threads = weakref.WeakSet()
        self.cleanup_scheduled = False
    
    def register_imageio_reader(self, reader):
        if reader:
            self.imageio_readers.add(reader)
    
    def register_video_player(self, player):
        if player:
            self.video_players.add(player)
    
    def register_temp_file(self, file_path):
        if file_path:
            self.temp_files.add(file_path)
    
    def register_thread(self, thread):
        if thread:
            self.background_threads.add(thread)
    
    def cleanup_imageio_readers(self):
        cleaned = 0
        try:
            readers_copy = list(self.imageio_readers)
            
            for reader in readers_copy:
                try:
                    if reader and hasattr(reader, 'close'):
                        reader.close()
                        cleaned += 1
                except Exception as e:
                    print(f"Error closing ImageIO reader: {e}")
            
            self.imageio_readers.clear()
            
            # PERFORMANCE FIX: Commented out excessive logging
            # if cleaned > 0:
            #     print(f"✅ Cleaned up {cleaned} ImageIO readers")
                
        except Exception as e:
            print(f"Error in ImageIO cleanup: {e}")
        
        return cleaned
    
    def cleanup_video_players(self):
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
            
            # PERFORMANCE FIX: Commented out excessive logging
            # if cleaned > 0:
            #     print(f"✅ Cleaned up {cleaned} video players")
                
        except Exception as e:
            print(f"Error in video player cleanup: {e}")
        
        return cleaned
    
    def cleanup_temp_files(self):
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
        
        # PERFORMANCE FIX: Commented out excessive logging
        # if cleaned > 0:
        #     print(f"✅ Cleaned up {cleaned} temp files")
        
        return cleaned
    
    def full_cleanup(self):
        # PERFORMANCE FIX: Commented out excessive logging
        # print("🧹 Starting full resource cleanup...")
        
        total_cleaned = 0
        total_cleaned += self.cleanup_imageio_readers()
        total_cleaned += self.cleanup_video_players()
        total_cleaned += self.cleanup_temp_files()
        
        collected = gc.collect()
        
        # PERFORMANCE FIX: Commented out excessive logging
        # print(f"✅ Full cleanup complete: {total_cleaned} resources, {collected} objects collected")
        return total_cleaned
    
    def schedule_periodic_cleanup(self):
        if not self.cleanup_scheduled:
            self.cleanup_scheduled = True
            Clock.schedule_interval(self.periodic_cleanup, 30)
    
    def periodic_cleanup(self, dt):
        try:
            reader_count = len(self.imageio_readers)
            player_count = len(self.video_players)
            temp_count = len(self.temp_files)
            
            if reader_count > 5 or player_count > 3 or temp_count > 10:
                # PERFORMANCE FIX: Commented out excessive logging
                # print(f"🧹 Periodic cleanup: {reader_count} readers, {player_count} players, {temp_count} temp files")
                self.full_cleanup()
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")

class VideoVaultCore:
    def __init__(self, app_instance):
        self.app = app_instance
        self.vault_dir = self.get_vault_directory()
        self.ensure_vault_directory()
        self.processing = False
        
        self.resource_manager = ResourceManager()
        self.resource_manager.schedule_periodic_cleanup()
        
        self.video_info_cache = {}
        self.video_info_cache_file = os.path.join(self.vault_dir, 'video_info_cache.json')
        self.load_video_info_cache()
        
        self.widget_references = weakref.WeakSet()
    
    def register_widget(self, widget):
        if widget:
            self.widget_references.add(widget)
    
    def cleanup_widgets(self):
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
        
        # PERFORMANCE FIX: Commented out excessive logging
        # if cleaned > 0:
        #     print(f"✅ Cleaned up {cleaned} widgets")
        
        return cleaned
    
    def get_vault_directory(self):
        """Get vault directory - Desktop only"""
        # SIMPLIFIED: Desktop-only logic
        if hasattr(self.app, 'secure_storage'):
            return self.app.secure_storage.get_vault_directory('videos')
        
        # Default desktop vault directory
        return os.path.join(os.getcwd(), 'vault_videos')
    
    def ensure_vault_directory(self):
        try:
            if not os.path.exists(self.vault_dir):
                os.makedirs(self.vault_dir)
            thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
        except Exception as e:
            print(f"Error creating vault directory: {e}")
    
    # REMOVED: request_permissions method completely
    # Not needed on desktop platforms
    
    def load_video_info_cache(self):
        try:
            if os.path.exists(self.video_info_cache_file):
                with open(self.video_info_cache_file, 'r') as f:
                    self.video_info_cache = json.load(f)
                # PERFORMANCE FIX: Commented out excessive logging
                # print(f"✅ Loaded video info cache: {len(self.video_info_cache)} entries")
            else:
                self.video_info_cache = {}
        except Exception as e:
            print(f"Error loading video info cache: {e}")
            self.video_info_cache = {}

    def save_video_info_cache(self):
        try:
            with open(self.video_info_cache_file, 'w') as f:
                json.dump(self.video_info_cache, f, indent=2)
        except Exception as e:
            print(f"Error saving video info cache: {e}")
    
    def is_valid_video(self, file_path):
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.ogg', '.ogv']
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    def generate_thumbnail_safe(self, video_path):
        try:
            thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
            filename = os.path.splitext(os.path.basename(video_path))[0]
            thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
            
            if os.path.exists(thumb_path):
                # PERFORMANCE FIX: Commented out excessive logging
                # print(f"✅ Thumbnail already exists: {thumb_path}")
                return thumb_path
            
            # PERFORMANCE FIX: Commented out excessive logging
            # print(f"🔄 Generating new thumbnail for: {video_path}")
            
            if IMAGEIO_AVAILABLE:
                reader = None
                try:
                    reader = imageio.get_reader(video_path, 'ffmpeg')
                    self.resource_manager.register_imageio_reader(reader)
                    
                    frame = reader.get_data(0)
                    
                    if frame is not None:
                        pil_image = PILImage.fromarray(frame)
                        
                        width, height = pil_image.size
                        aspect_ratio = width / height
                        
                        if aspect_ratio > 1:
                            new_width = 150
                            new_height = int(150 / aspect_ratio)
                        else:
                            new_height = 150
                            new_width = int(150 * aspect_ratio)
                        
                        thumbnail = pil_image.resize((new_width, new_height), PILImage.Resampling.BILINEAR)
                        thumbnail.save(thumb_path, 'JPEG', quality=75, optimize=True)
                        # PERFORMANCE FIX: Commented out excessive logging
                        # print(f"✅ Thumbnail generated: {thumb_path}")
                    
                except Exception as e:
                    print(f"ImageIO thumbnail generation error: {e}")
                    self.generate_placeholder_thumbnail(thumb_path)
                finally:
                    if reader is not None:
                        try:
                            reader.close()
                            # PERFORMANCE FIX: Commented out excessive logging
                            # print(f"🧹 ImageIO reader closed: {os.path.basename(video_path)}")
                        except Exception as cleanup_error:
                            # PERFORMANCE FIX: Commented out excessive logging
                            # print(f"⚠️ Error closing reader: {cleanup_error}")
                            pass
                        reader = None
            else:
                self.generate_placeholder_thumbnail(thumb_path)
            
            return thumb_path
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None
    
    def generate_placeholder_thumbnail(self, thumb_path):
        try:
            img = PILImage.new('RGB', (150, 110), color='#37474F')
            
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                font = ImageFont.load_default()
                
                text = "VIDEO"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                position = ((150 - text_width) // 2, (110 - text_height) // 2)
                draw.text(position, text, fill='white', font=font)
                
            except ImportError:
                pass
            
            img.save(thumb_path, 'JPEG', quality=60, optimize=True)
            # PERFORMANCE FIX: Commented out excessive logging
            # print(f"✅ Placeholder thumbnail created: {thumb_path}")
        except Exception as e:
            print(f"Error generating placeholder thumbnail: {e}")
    
    def get_thumbnail_path(self, video_path):
        thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
        filename = os.path.splitext(os.path.basename(video_path))[0]
        thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
        
        if os.path.exists(thumb_path):
            return thumb_path
        else:
            return None
    
    def generate_thumbnails_background(self, video_paths, callback=None):
        def thumbnail_worker():
            generated_count = 0
            for video_path in video_paths:
                try:
                    if self.generate_thumbnail_safe(video_path):
                        generated_count += 1
                        if generated_count % 3 == 0 and callback:
                            Clock.schedule_once(lambda dt: callback(), 0)
                except Exception as e:
                    print(f"Background thumbnail error for {video_path}: {e}")
            
            # PERFORMANCE FIX: Commented out excessive logging
            # print(f"✅ Background thumbnail generation complete: {generated_count}/{len(video_paths)}")
            if callback:
                Clock.schedule_once(lambda dt: callback(), 0)
        
        thread = threading.Thread(target=thumbnail_worker)
        thread.daemon = True
        self.resource_manager.register_thread(thread)
        thread.start()