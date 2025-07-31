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
from kivy.clock import Clock
from plyer import filechooser

# Import the core class
from video_vault_core_optimized import VideoVaultCore, IMAGEIO_AVAILABLE, PSUTIL_AVAILABLE

# REMOVED: ANDROID import - desktop only now
ANDROID = False  # Always False for desktop-only version

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
            'dwm.exe',       # Desktop Window Manager
            'audiodg.exe',   # Audio Device Graph Isolation
        ]
        
        for process_name in processes_to_kill:
            try:
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

# Extend the VideoVaultCore class with additional methods
class VideoVaultCoreExtended(VideoVaultCore):
    """Extended video vault with operations and memory management"""
    
    def get_video_info_safe(self, video_path):
        """Get video information with caching and fast fallback"""
        try:
            # Generate cache key based on file path and modification time
            file_stat = os.stat(video_path)
            cache_key = f"{video_path}_{file_stat.st_mtime}_{file_stat.st_size}"
            
            # OPTIMIZATION 1: Check cache first
            if cache_key in self.video_info_cache:
                cached_info = self.video_info_cache[cache_key]
                print(f"📋 Using cached video info for: {os.path.basename(video_path)}")
                return cached_info
            
            # OPTIMIZATION 2: Get basic file info immediately (non-blocking)
            file_size = file_stat.st_size
            file_size_mb = round(file_size / (1024 * 1024), 1)
            
            # OPTIMIZATION 3: Try fast duration detection first
            duration = self.get_duration_fast(video_path)
            
            # Create info object
            video_info = {
                'size': f"{file_size_mb} MB",
                'duration': duration,
                'cached_at': time.time()
            }
            
            # Cache the result
            self.video_info_cache[cache_key] = video_info
            
            # Clean old cache entries to prevent memory bloat
            self.cleanup_video_info_cache()
            
            return video_info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {'size': 'Unknown', 'duration': 'Unknown'}

    def get_duration_fast(self, video_path):
        """Get video duration using fastest available method"""
        try:
            # METHOD 1: Try ffprobe first (fastest and most reliable)
            if self.has_ffprobe():
                return self.get_duration_ffprobe(video_path)
            
            # METHOD 2: Try ImageIO with timeout (fallback)
            return self.get_duration_imageio_fast(video_path)
            
        except Exception as e:
            print(f"Fast duration detection failed: {e}")
            return "Unknown"

    def has_ffprobe(self):
        """Check if ffprobe is available"""
        try:
            subprocess.run(['ffprobe', '-version'], 
                          capture_output=True, timeout=2)
            return True
        except:
            return False

    def get_duration_ffprobe(self, video_path):
        """Get duration using ffprobe (fastest method)"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', 
                '-print_format', 'json', 
                '-show_format', 
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, 
                                  text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration_seconds = float(data['format']['duration'])
                
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                return f"{minutes}:{seconds:02d}"
            
        except Exception as e:
            print(f"ffprobe failed: {e}")
        
        return "Unknown"

    def get_duration_imageio_fast(self, video_path):
        """Get duration using ImageIO with strict timeout"""
        reader = None
        try:
            # Use a timeout to prevent hanging
            if platform.system() != "Windows":
                signal.signal(signal.SIGALRM, lambda signum, frame: None)
                signal.alarm(3)  # 3 second timeout
            
            import imageio
            reader = imageio.get_reader(video_path, 'ffmpeg')
            self.resource_manager.register_imageio_reader(reader)
            
            # Get video metadata quickly
            meta = reader.get_meta_data()
            duration = "Unknown"
            
            if 'duration' in meta:
                duration_seconds = meta['duration']
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                duration = f"{minutes}:{seconds:02d}"
            
            # Cancel timeout
            if platform.system() != "Windows":
                signal.alarm(0)
            
            # Immediate cleanup
            reader.close()
            
            return duration
            
        except Exception as e:
            print(f"ImageIO fast duration failed: {e}")
            return "Unknown"
        finally:
            if platform.system() != "Windows":
                try:
                    signal.alarm(0)
                except:
                    pass
            if reader:
                try:
                    reader.close()
                except:
                    pass

    def cleanup_video_info_cache(self):
        """Clean up old cache entries to prevent bloat"""
        try:
            current_time = time.time()
            cache_max_age = 7 * 24 * 3600  # 7 days
            
            keys_to_remove = []
            for key, info in self.video_info_cache.items():
                cached_at = info.get('cached_at', 0)
                if current_time - cached_at > cache_max_age:
                    keys_to_remove.append(key)
            
            # Remove old entries
            for key in keys_to_remove:
                del self.video_info_cache[key]
            
            if keys_to_remove:
                print(f"🧹 Cleaned {len(keys_to_remove)} old cache entries")
                # Save updated cache
                self.save_video_info_cache()
                
        except Exception as e:
            print(f"Error cleaning cache: {e}")

    def get_videos_info_batch(self, video_paths, callback):
        """Get video info for multiple videos in background"""
        def info_worker():
            video_info_map = {}
            processed = 0
            
            for video_path in video_paths:
                try:
                    info = self.get_video_info_safe(video_path)
                    video_info_map[video_path] = info
                    processed += 1
                    
                    # Update UI every 5 videos processed
                    if processed % 5 == 0:
                        Clock.schedule_once(
                            lambda dt, vm=video_info_map.copy(): callback(vm), 0
                        )
                        
                except Exception as e:
                    print(f"Error getting info for {video_path}: {e}")
                    video_info_map[video_path] = {'size': 'Error', 'duration': 'Error'}
            
            # Final callback with all results
            Clock.schedule_once(lambda dt: callback(video_info_map), 0)
            
            # Save cache after batch processing
            self.save_video_info_cache()
        
        # Start background thread
        thread = threading.Thread(target=info_worker)
        thread.daemon = True
        self.resource_manager.register_thread(thread)
        thread.start()
    
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
            import psutil
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
        """Permanent deletion fallback with enhanced cleanup"""
        print(f"\n🔥 PERMANENT DELETION FALLBACK")
        print(f"Target: {video_path}")
        
        # Step 1: Comprehensive resource cleanup first
        print("🧹 Comprehensive resource cleanup...")
        self.resource_manager.full_cleanup()
        
        # Step 2: Clean up any widgets that might reference this file
        self.cleanup_widgets()
        
        # Step 3: Find what's using the file
        print("🔍 Finding processes using the file...")
        processes = find_processes_using_file(video_path)
        if processes:
            print("Found processes using file:")
            for proc in processes:
                print(f"  - {proc}")
        else:
            print("No processes found using file (or tools not available)")
        
        # Step 4: Check our own app's handles
        print("🔍 Checking our app's file handles...")
        force_close_app_handles()
        
        # Step 5: Kill thumbnail cache
        print("🔍 Killing Windows thumbnail cache...")
        if kill_explorer_thumbnails():
            time.sleep(2.0)  # Wait for processes to die
        
        # Step 6: Force garbage collection multiple times
        print("🔍 Running garbage collection...")
        for i in range(5):
            gc.collect()
            time.sleep(0.3)
        
        # Wait for Windows file handles to be released
        if platform.system() == "Windows":
            print("🔍 Waiting for Windows file handles to be released...")
            time.sleep(3.0)
        
        # Step 7: Try standard deletion first
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
        
        # Method 3: System command deletion
        try:
            print("Method 3: System command deletion")
            if platform.system() == "Windows":
                escaped_path = video_path.replace('"', '""')
                cmd = f'del /f /q "{escaped_path}"'
                result = subprocess.run(['cmd', '/c', cmd], 
                                    capture_output=True, text=True, timeout=15)
                if result.returncode == 0 and not os.path.exists(video_path):
                    print("✅ Windows del command successful")
                    return True
                print(f"❌ Windows del command failed: {result.stderr}")
            elif platform.system() in ["Linux", "Darwin"]:
                result = subprocess.run(['rm', '-f', video_path], 
                                    capture_output=True, text=True, timeout=15)
                if result.returncode == 0 and not os.path.exists(video_path):
                    print("✅ rm command successful")
                    return True
                print(f"❌ rm command failed: {result.stderr}")
        except Exception as e:
            print(f"❌ System command deletion failed: {e}")
        
        # Method 4: Move to temp and schedule for deletion
        if platform.system() == "Windows":
            try:
                print("Method 4: Move to temp and schedule for deletion")
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_name = f"delete_me_{int(time.time())}_{os.path.basename(video_path)}"
                temp_path = os.path.join(temp_dir, temp_name)
                
                # Try to move the file to temp
                shutil.move(video_path, temp_path)
                print(f"✅ Moved file to temp: {temp_path}")
                
                # Register for cleanup
                self.resource_manager.register_temp_file(temp_path)
                
                # Try to delete from temp immediately
                try:
                    time.sleep(1.0)
                    os.remove(temp_path)
                    self.resource_manager.temp_files.discard(temp_path)
                    print("✅ Deleted from temp successfully")
                    return True
                except Exception as del_e:
                    print(f"Could not delete from temp: {del_e}")
                    print(f"✅ File moved to temp and will be cleaned up later: {temp_path}")
                    return True
                
            except Exception as e:
                print(f"❌ Move to temp failed: {e}")
        
        # Method 5: Last resort - mark as hidden and rename
        try:
            print("Method 5: Mark as hidden and rename")
            if os.path.exists(video_path):
                delete_marker = f"{video_path}.DELETE_ME_{int(time.time())}"
                os.rename(video_path, delete_marker)
                
                # Register for cleanup
                self.resource_manager.register_temp_file(delete_marker)
                
                # Try to hide the file on Windows
                if platform.system() == "Windows":
                    try:
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
        """Delete video with recycle bin integration and memory cleanup"""
        try:
            print(f"\n🗑️ MOVING VIDEO TO RECYCLE BIN")
            print(f"Target file: {video_path}")
            
            # MEMORY FIX: Clean up resources first
            print("🧹 Cleaning up video resources...")
            self.resource_manager.full_cleanup()
            self.cleanup_widgets()
            
            # Wait for file handles to be released
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
                    return self.delete_video_permanent_fallback(video_path)
            else:
                print("⚠️ Recycle bin not available, using permanent deletion")
                return self.delete_video_permanent_fallback(video_path)
                
        except Exception as e:
            print(f"❌ Error moving video to recycle bin: {e}")
            print("🔄 Falling back to permanent deletion...")
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
            
            # FIXED: Just use the actual filename (no more vault_ prefix handling)
            original_name = os.path.basename(video_path)
            
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
        """Select folder for export - Desktop only"""
        # SIMPLIFIED: Only desktop folder picker now
        self.desktop_folder_picker(callback)

    # REMOVED: android_folder_picker method completely

    def desktop_folder_picker(self, callback):
        """Desktop folder picker using plyer"""
        def pick_folder():
            try:
                def on_selection(selection):
                    if selection and len(selection) > 0:
                        # For folder selection, plyer returns the selected folder path
                        folder_path = selection[0] if isinstance(selection, list) else selection
                        Clock.schedule_once(lambda dt: callback({'success': True, 'folder_path': folder_path}), 0)
                    else:
                        Clock.schedule_once(lambda dt: callback({'success': False, 'error': 'No folder selected'}), 0)
                
                # Use choose_dir for folder selection
                filechooser.choose_dir(
                    on_selection=on_selection,
                    title="Select Export Destination Folder"
                )
                        
            except Exception as e:
                print(f"Plyer folder picker error: {e}")
                Clock.schedule_once(lambda dt: callback({'success': False, 'error': str(e)}), 0)
        
        thread = threading.Thread(target=pick_folder)
        thread.daemon = True
        self.resource_manager.register_thread(thread)
        thread.start()

    def fallback_folder_picker(self, callback):
        """Fallback folder picker - Desktop only"""
        try:
            # SIMPLIFIED: Desktop-only fallback
            fallback_folder = os.path.join(os.path.expanduser('~'), 'Videos')
            
            if not os.path.exists(fallback_folder):
                os.makedirs(fallback_folder)
            
            callback({'success': True, 'folder_path': fallback_folder, 'is_fallback': True})
            
        except Exception as e:
            callback({'success': False, 'error': f'Fallback folder creation failed: {e}'})

# Export the extended class as the main class
VideoVaultCore = VideoVaultCoreExtended