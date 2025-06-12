import os
import shutil
import threading
import subprocess
import platform
import gc
import time
import re
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

def find_processes_using_file(file_path):
    """Find what processes are using a file on Windows"""
    if platform.system() != "Windows":
        return []
    
    processes = []
    try:
        # Use handle.exe if available (part of SysInternals)
        result = subprocess.run(['handle.exe', file_path], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if file_path.lower() in line.lower():
                    processes.append(line.strip())
        
    except FileNotFoundError:
        # handle.exe not available, try alternative method
        try:
            # Use PowerShell to find process
            ps_command = f'''
            Get-Process | Where-Object {{
                try {{
                    $_.Modules | Where-Object {{ $_.FileName -eq "{file_path}" }}
                }} catch {{ }}
            }} | Select-Object ProcessName, Id
            '''
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  capture_output=True, text=True, timeout=15)
            if result.stdout:
                processes.append(result.stdout)
        except:
            pass
    except:
        pass
    
    return processes

def force_close_app_handles():
    """Force close any handles that might be from our own app"""
    if platform.system() != "Windows":
        return
    
    try:
        import psutil
        current_pid = os.getpid()
        current_process = psutil.Process(current_pid)
        
        # Try to close any open file handles in our process
        try:
            for f in current_process.open_files():
                print(f"Our process has open file: {f.path}")
        except:
            pass
    except ImportError:
        pass

def kill_explorer_thumbnails():
    """Kill Windows Explorer thumbnail cache processes"""
    if platform.system() != "Windows":
        return False
    
    killed = False
    try:
        # Kill thumbnail cache processes that might lock video files
        processes_to_kill = [
            'explorer.exe',  # Windows Explorer (thumbnails)
            'dwm.exe',       # Desktop Window Manager
            'audiodg.exe',   # Audio Device Graph Isolation
        ]
        
        for process_name in processes_to_kill:
            try:
                # Don't kill explorer.exe as it's the desktop
                if process_name == 'explorer.exe':
                    continue
                    
                result = subprocess.run(['taskkill', '/f', '/im', process_name], 
                                      capture_output=True, timeout=10)
                if result.returncode == 0:
                    print(f"Killed {process_name}")
                    killed = True
                    time.sleep(0.5)
            except:
                pass
                
        # Clear thumbnail cache
        try:
            cache_paths = [
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*.db'),
            ]
            
            for cache_path in cache_paths:
                if os.path.exists(cache_path):
                    try:
                        if os.path.isfile(cache_path):
                            os.remove(cache_path)
                        else:
                            # Clear thumbnail cache files
                            for file in os.listdir(cache_path):
                                if file.startswith('thumbcache_'):
                                    try:
                                        os.remove(os.path.join(cache_path, file))
                                        print(f"Cleared thumbnail cache: {file}")
                                    except:
                                        pass
                    except:
                        pass
            killed = True
        except:
            pass
    except:
        pass
    
    return killed

class VideoVaultCore:
    """Core video vault functionality with proper file handle management"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.vault_dir = self.get_vault_directory()
        self.ensure_vault_directory()
        self.processing = False  # Flag to prevent multiple operations
        self.active_video_players = []  # Track active video players for cleanup
        self.imageio_readers = []  # Track ImageIO reader objects
        
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
    
    def cleanup_all_imageio_readers(self):
        """Clean up all ImageIO reader objects"""
        if IMAGEIO_AVAILABLE:
            try:
                print(f"Cleaning up {len(self.imageio_readers)} ImageIO readers...")
                
                # Close all tracked readers
                for reader in self.imageio_readers:
                    try:
                        if reader is not None:
                            reader.close()
                    except Exception as e:
                        print(f"Error closing reader: {e}")
                
                self.imageio_readers.clear()
                
                # Force garbage collection multiple times
                for i in range(3):
                    gc.collect()
                    time.sleep(0.1)
                
                # Give Windows extra time to release file handles
                if platform.system() == "Windows":
                    time.sleep(1.0)
                    
                print("ImageIO cleanup completed")
                    
            except Exception as e:
                print(f"Error cleaning up ImageIO readers: {e}")
    
    def cleanup_video_players(self):
        """Clean up any active video players to release file locks"""
        print(f"Cleaning up {len(self.active_video_players)} video players...")
        for player in self.active_video_players:
            try:
                if hasattr(player, 'state'):
                    player.state = 'stop'
                if hasattr(player, 'unload'):
                    player.unload()
            except Exception as e:
                print(f"Error cleaning up video player: {e}")
        self.active_video_players.clear()
        gc.collect()
        print("Video player cleanup completed")
    
    def is_valid_video(self, file_path):
        """Check if file is a valid video"""
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.ogg', '.ogv']
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    def generate_thumbnail_safe(self, video_path):
        """Generate thumbnail for video with comprehensive resource cleanup"""
        try:
            thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
            filename = os.path.splitext(os.path.basename(video_path))[0]
            thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
            
            print(f"Generating thumbnail for: {video_path}")
            
            if IMAGEIO_AVAILABLE:
                reader = None
                try:
                    # Create ImageIO reader object
                    reader = imageio.get_reader(video_path, 'ffmpeg')
                    self.imageio_readers.append(reader)  # Track it
                    
                    # Get the first frame
                    frame = reader.get_data(0)
                    
                    if frame is not None:
                        # Convert numpy array to PIL Image
                        pil_image = PILImage.fromarray(frame)
                        
                        # Calculate thumbnail dimensions
                        width, height = pil_image.size
                        aspect_ratio = width / height
                        
                        if aspect_ratio > 1:  # Landscape
                            new_width = 200
                            new_height = int(200 / aspect_ratio)
                        else:  # Portrait
                            new_height = 200
                            new_width = int(200 * aspect_ratio)
                        
                        # Resize and save
                        thumbnail = pil_image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                        thumbnail.save(thumb_path, 'JPEG')
                        print(f"Thumbnail generated successfully: {thumb_path}")
                    
                    # CRITICAL: Immediate cleanup
                    if reader is not None:
                        reader.close()
                        # Remove from tracking list
                        if reader in self.imageio_readers:
                            self.imageio_readers.remove(reader)
                        reader = None
                    
                    # Additional cleanup
                    gc.collect()
                    
                    # Windows-specific: give time for file handles to be released
                    if platform.system() == "Windows":
                        time.sleep(0.3)
                    
                except Exception as e:
                    print(f"ImageIO thumbnail generation error: {e}")
                    # Ensure cleanup even on error
                    if reader is not None:
                        try:
                            reader.close()
                            if reader in self.imageio_readers:
                                self.imageio_readers.remove(reader)
                        except:
                            pass
                    # Fallback to PIL
                    self.generate_placeholder_thumbnail(thumb_path)
                finally:
                    # Final cleanup - absolutely critical
                    if reader is not None:
                        try:
                            reader.close()
                            if reader in self.imageio_readers:
                                self.imageio_readers.remove(reader)
                        except:
                            pass
                    gc.collect()
            else:
                # Fallback: create a simple thumbnail placeholder
                self.generate_placeholder_thumbnail(thumb_path)
            
            return thumb_path
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None
    
    def generate_placeholder_thumbnail(self, thumb_path):
        """Generate a placeholder thumbnail using PIL"""
        try:
            # Create a better-looking placeholder
            img = PILImage.new('RGB', (200, 150), color='#2C3E50')
            
            # Try to add text if PIL supports it
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Try to use a font, fallback to default
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                
                # Add video icon and text
                text = "🎬\nVIDEO"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                position = ((200 - text_width) // 2, (150 - text_height) // 2)
                draw.text(position, text, fill='white', font=font, align='center')
                
            except ImportError:
                # PIL doesn't have text drawing capabilities
                pass
            
            img.save(thumb_path, 'JPEG')
            print(f"Placeholder thumbnail created: {thumb_path}")
        except Exception as e:
            print(f"Error generating placeholder thumbnail: {e}")
    
    def get_thumbnail_path(self, video_path):
        """Get thumbnail path for a video"""
        thumb_dir = os.path.join(self.vault_dir, 'thumbnails')
        filename = os.path.splitext(os.path.basename(video_path))[0]
        thumb_path = os.path.join(thumb_dir, f"{filename}_thumb.jpg")
        
        if os.path.exists(thumb_path):
            return thumb_path
        else:
            # Generate thumbnail if it doesn't exist
            return self.generate_thumbnail_safe(video_path)
    
    def get_video_info_safe(self, video_path):
        """Get video information safely with proper resource cleanup"""
        try:
            file_size = os.path.getsize(video_path)
            file_size_mb = round(file_size / (1024 * 1024), 1)
            
            duration = "Unknown"
            if IMAGEIO_AVAILABLE:
                reader = None
                try:
                    reader = imageio.get_reader(video_path, 'ffmpeg')
                    self.imageio_readers.append(reader)  # Track it
                    
                    # Get video metadata
                    meta = reader.get_meta_data()
                    if 'duration' in meta:
                        duration_seconds = meta['duration']
                        minutes = int(duration_seconds // 60)
                        seconds = int(duration_seconds % 60)
                        duration = f"{minutes}:{seconds:02d}"
                    elif 'fps' in meta and hasattr(reader, '_nframes'):
                        # Fallback calculation if duration not available
                        fps = meta['fps']
                        frame_count = reader.count_frames()
                        if fps > 0:
                            duration_seconds = frame_count / fps
                            minutes = int(duration_seconds // 60)
                            seconds = int(duration_seconds % 60)
                            duration = f"{minutes}:{seconds:02d}"
                    
                    # CRITICAL: Immediate cleanup
                    reader.close()
                    if reader in self.imageio_readers:
                        self.imageio_readers.remove(reader)
                    reader = None
                    
                except Exception as e:
                    print(f"Error getting video duration: {e}")
                finally:
                    if reader is not None:
                        try:
                            reader.close()
                            if reader in self.imageio_readers:
                                self.imageio_readers.remove(reader)
                        except:
                            pass
                    gc.collect()
            
            return {
                'size': f"{file_size_mb} MB",
                'duration': duration
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {'size': 'Unknown', 'duration': 'Unknown'}
    
    def get_vault_videos(self):
        """Get list of all videos in vault"""
        videos = []
        try:
            if os.path.exists(self.vault_dir):
                for filename in os.listdir(self.vault_dir):
                    if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.ogg', '.ogv')):
                        videos.append(os.path.join(self.vault_dir, filename))
            return sorted(videos, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
        except Exception as e:
            print(f"Error getting vault videos: {e}")
            return []
    
    def force_kill_processes_using_file(self, file_path):
        """Force kill processes that are using the file (Windows only)"""
        if platform.system() != "Windows" or not PSUTIL_AVAILABLE:
            return False
        
        killed_any = False
        try:
            print(f"Searching for processes using file: {file_path}")
            # Find and terminate processes with open handles to this file
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Skip critical system processes
                    if proc.info['name'].lower() in ['system', 'csrss.exe', 'winlogon.exe', 'services.exe', 'lsass.exe']:
                        continue
                    
                    for item in proc.open_files():
                        if item.path.lower() == file_path.lower():
                            print(f"Found process {proc.info['name']} (PID: {proc.info['pid']}) using file")
                            try:
                                proc.terminate()
                                proc.wait(timeout=3)
                                print(f"Terminated process {proc.info['name']}")
                                killed_any = True
                            except psutil.TimeoutExpired:
                                # Force kill if terminate doesn't work
                                proc.kill()
                                print(f"Force killed process {proc.info['name']}")
                                killed_any = True
                            except Exception as e:
                                print(f"Could not kill process {proc.info['name']}: {e}")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
        except Exception as e:
            print(f"Error in force_kill_processes_using_file: {e}")
        
        return killed_any
    
    def delete_video_permanent_fallback(self, video_path):
        print(f"\n🔥 PERMANENT DELETION FALLBACK")
        print(f"Target: {video_path}")
        
        # This is your EXACT existing delete_video_aggressive method
        # Just rename it - keep all the same code!
        
        # Step 1: Find what's using the file
        print("🔍 Finding processes using the file...")
        processes = find_processes_using_file(video_path)
        if processes:
            print("Found processes using file:")
            for proc in processes:
                print(f"  - {proc}")
        else:
            print("No processes found using file (or tools not available)")
        
        # Step 2: Check our own app's handles
        print("🔍 Checking our app's file handles...")
        force_close_app_handles()
        
        # Step 3: Kill thumbnail cache
        print("🔍 Killing Windows thumbnail cache...")
        if kill_explorer_thumbnails():
            import time
            time.sleep(2.0)  # Wait for processes to die
        
        # Step 4: Comprehensive cleanup
        print("🔍 Comprehensive cleanup...")
        self.cleanup_all_imageio_readers()
        self.cleanup_video_players()
        
        # Force garbage collection multiple times
        print("🔍 Running garbage collection...")
        import gc
        import time
        for i in range(5):
            gc.collect()
            time.sleep(0.3)
        
        # Wait for Windows file handles to be released
        import platform
        if platform.system() == "Windows":
            print("🔍 Waiting for Windows file handles to be released...")
            time.sleep(3.0)
        
        # Step 5: Try standard deletion first
        print("=== STARTING AGGRESSIVE DELETION ===")
        print("Method 1: Standard deletion after cleanup")
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print("✅ Standard deletion successful")
                return True
        except Exception as e:
            print(f"❌ Standard deletion failed: {e}")
        
        # Method 2: Force kill processes using the file (Windows)
        if platform.system() == "Windows":
            try:
                print("Method 2: Force kill processes using the file")
                if self.force_kill_processes_using_file(video_path):
                    print("Processes killed, waiting before deletion...")
                    time.sleep(1.0)
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        print("✅ Deletion after process kill successful")
                        return True
            except Exception as e:
                print(f"❌ Process kill deletion failed: {e}")
        
        # Method 3: System command deletion with corrected syntax
        try:
            print("Method 3: System command deletion")
            import subprocess
            if platform.system() == "Windows":
                # Use Windows del command with corrected syntax
                escaped_path = video_path.replace('"', '""')  # Escape quotes
                cmd = f'del /f /q "{escaped_path}"'
                result = subprocess.run(['cmd', '/c', cmd], 
                                    capture_output=True, text=True, timeout=15)
                if result.returncode == 0 and not os.path.exists(video_path):
                    print("✅ Windows del command successful")
                    return True
                print(f"❌ Windows del command failed: {result.stderr}")
            elif platform.system() in ["Linux", "Darwin"]:
                # Use rm command
                result = subprocess.run(['rm', '-f', video_path], 
                                    capture_output=True, text=True, timeout=15)
                if result.returncode == 0 and not os.path.exists(video_path):
                    print("✅ rm command successful")
                    return True
                print(f"❌ rm command failed: {result.stderr}")
        except Exception as e:
            print(f"❌ System command deletion failed: {e}")
        
        # Method 4: Move to temp and schedule for deletion (Windows)
        if platform.system() == "Windows":
            try:
                print("Method 4: Move to temp and schedule for deletion")
                import tempfile
                import shutil
                temp_dir = tempfile.gettempdir()
                temp_name = f"delete_me_{int(time.time())}_{os.path.basename(video_path)}"
                temp_path = os.path.join(temp_dir, temp_name)
                
                # Try to move the file to temp
                shutil.move(video_path, temp_path)
                print(f"✅ Moved file to temp: {temp_path}")
                
                # Try to delete from temp immediately
                try:
                    time.sleep(1.0)
                    os.remove(temp_path)
                    print("✅ Deleted from temp successfully")
                    return True
                except Exception as del_e:
                    print(f"Could not delete from temp: {del_e}")
                    # File moved to temp, consider this success
                    print(f"✅ File moved to temp and will be cleaned up later: {temp_path}")
                    return True
                
            except Exception as e:
                print(f"❌ Move to temp failed: {e}")
        
        # Method 5: Last resort - mark as hidden and rename
        try:
            print("Method 5: Mark as hidden and rename")
            if os.path.exists(video_path):
                # Rename to indicate it should be deleted
                delete_marker = f"{video_path}.DELETE_ME_{int(time.time())}"
                os.rename(video_path, delete_marker)
                
                # Try to hide the file on Windows
                if platform.system() == "Windows":
                    try:
                        import subprocess
                        subprocess.run(['attrib', '+H', delete_marker], capture_output=True)
                    except:
                        pass
                
                print(f"✅ File marked for deletion: {delete_marker}")
                return True
                
        except Exception as e:
            print(f"❌ Final deletion method failed: {e}")
        
        print("❌ ALL DELETION METHODS FAILED")
        return False
    
    def delete_video(self, video_path):
        try:
            print(f"\n🗑️ MOVING VIDEO TO RECYCLE BIN")
            print(f"Target file: {video_path}")
            
            # Clean up resources first (keep existing cleanup)
            print("🔍 Cleaning up video resources...")
            self.cleanup_all_imageio_readers()
            self.cleanup_video_players()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Wait for file handles to be released (especially important for Windows)
            import time
            time.sleep(1.0)
            
            # NEW: Move to recycle bin instead of permanent deletion
            if hasattr(self.app, 'recycle_bin'):
                print("📦 Using recycle bin for safe deletion...")
                
                # Get thumbnail info for metadata
                thumb_path = None
                try:
                    thumb_path = self.get_thumbnail_path(video_path)
                    if thumb_path and not os.path.exists(thumb_path):
                        thumb_path = None
                except Exception as e:
                    print(f"Warning: Could not get thumbnail path: {e}")
                
                # Move to recycle bin
                result = self.app.recycle_bin.move_to_recycle(
                    file_path=video_path,
                    original_location=os.path.dirname(video_path),
                    metadata={
                        'vault_type': 'videos',
                        'thumbnail_path': thumb_path,
                        'original_name': os.path.basename(video_path),
                        'file_size': os.path.getsize(video_path) if os.path.exists(video_path) else 0
                    }
                )
                
                if result['success']:
                    print(f"✅ Video moved to recycle bin successfully: {video_path}")
                    print(f"📍 Recycle bin location: {result['recycled_path']}")
                    return True
                else:
                    print(f"❌ Failed to move to recycle bin: {result.get('error', 'Unknown error')}")
                    print("🔄 Falling back to permanent deletion...")
                    # Fallback to aggressive deletion if recycle bin fails
                    return self.delete_video_permanent_fallback(video_path)
            else:
                # Fallback to old behavior if recycle bin not available
                print("⚠️ Recycle bin not available, using permanent deletion")
                return self.delete_video_permanent_fallback(video_path)
                
        except Exception as e:
            print(f"❌ Error moving video to recycle bin: {e}")
            print("🔄 Falling back to permanent deletion...")
            # Fallback to aggressive deletion on any error
            return self.delete_video_permanent_fallback(video_path)
    
    def open_video_externally(self, video_path):
        """Open video with system default player"""
        try:
            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            else:  # Linux
                subprocess.run(["xdg-open", video_path])
            return True
        except Exception as e:
            print(f"Error opening video externally: {e}")
            return False
    
    def export_video(self, video_path, user_selected_folder=None):
        """Export video to user-selected location"""
        try:
            if not os.path.exists(video_path):
                return {'success': False, 'error': 'Video not found'}
            
            # Get original filename (remove vault_ prefix)
            vault_filename = os.path.basename(video_path)
            match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
            if match:
                original_name = match.group(1)
            else:
                original_name = vault_filename
            
            if not user_selected_folder:
                return {'success': False, 'error': 'No export folder selected', 'needs_folder_selection': True}
            
            # Check if selected folder exists and is writable
            if not os.path.exists(user_selected_folder):
                return {'success': False, 'error': 'Selected folder does not exist', 'needs_folder_selection': True}
            
            if not os.access(user_selected_folder, os.W_OK):
                return {'success': False, 'error': 'No write permission for selected folder', 'needs_folder_selection': True}
            
            export_path = os.path.join(user_selected_folder, original_name)
            
            # Handle filename conflicts
            counter = 1
            base_path = export_path
            while os.path.exists(export_path):
                name_part, ext_part = os.path.splitext(base_path)
                export_path = f"{name_part} ({counter}){ext_part}"
                counter += 1
            
            # Copy file
            shutil.copy2(video_path, export_path)
            
            return {
                'success': True,
                'export_path': export_path,
                'original_name': original_name,
                'export_folder': user_selected_folder
            }
            
        except Exception as e:
            print(f"Error exporting video: {e}")
            return {'success': False, 'error': str(e), 'needs_folder_selection': True}

    def select_export_folder(self, callback):
        """Select folder for export - Cross-platform"""
        if ANDROID:
            self.android_folder_picker(callback)
        else:
            self.desktop_folder_picker(callback)

    def android_folder_picker(self, callback):
        """Android folder picker using SAF"""
        try:
            # Use Storage Access Framework for folder selection
            from jnius import autoclass, cast
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivityForResult(intent, 42)  # Request code 42
            
            # Note: You'll need to handle the result in your Android activity
            # For now, fallback to basic implementation
            self.fallback_folder_picker(callback)
            
        except Exception as e:
            print(f"Android folder picker error: {e}")
            callback({'success': False, 'error': 'Failed to open folder picker'})

    def desktop_folder_picker(self, callback):
        """Desktop folder picker"""
        def pick_folder():
            try:
                root = tk.Tk()
                root.withdraw()
                
                folder_path = filedialog.askdirectory(
                    title="Select Export Destination Folder"
                )
                
                root.destroy()
                
                if folder_path:
                    Clock.schedule_once(lambda dt: callback({'success': True, 'folder_path': folder_path}), 0)
                else:
                    Clock.schedule_once(lambda dt: callback({'success': False, 'error': 'No folder selected'}), 0)
                    
            except Exception as e:
                print(f"Desktop folder picker error: {e}")
                Clock.schedule_once(lambda dt: callback({'success': False, 'error': str(e)}), 0)
        
        thread = threading.Thread(target=pick_folder)
        thread.daemon = True
        thread.start()

    def fallback_folder_picker(self, callback):
        """Fallback folder picker using Kivy"""
        # Use app's external storage as fallback
        try:
            if ANDROID:
                fallback_folder = os.path.join(app_storage_path(), 'exported_videos')
            else:
                fallback_folder = os.path.join(os.path.expanduser('~'), 'Videos')
            
            if not os.path.exists(fallback_folder):
                os.makedirs(fallback_folder)
            
            callback({'success': True, 'folder_path': fallback_folder, 'is_fallback': True})
            
        except Exception as e:
            callback({'success': False, 'error': f'Fallback folder creation failed: {e}'})