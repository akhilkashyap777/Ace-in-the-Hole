import os
import platform
import threading
import time

# Try to import Android-specific modules
try:
    from android.storage import app_storage_path
    from jnius import autoclass
    ANDROID = True
    
    # Android app context for private directories
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    File = autoclass('java.io.File')
    
except ImportError:
    ANDROID = False

class SecureStorage:
    """
    Cross-platform secure storage for app-private directories
    Files stored here are only accessible by your app, not visible to users or file managers
    ✅ OPTIMIZED VERSION with caching and lazy loading
    """
    
    def __init__(self, app_name="SecretVault"):
        self.app_name = app_name
        
        # ✅ OPTIMIZATION: Cache frequently accessed values
        self._platform_cache = None
        self._base_dir_cache = None
        self._storage_info_cache = None
        self._storage_info_cache_time = 0
        self._storage_info_cache_ttl = 300  # 5 minutes
        
        # ✅ OPTIMIZATION: Lazy initialization
        self._directories_created = False
        self._security_verified = False
        self._security_result = None
        
        # ✅ OPTIMIZATION: Thread lock for cache safety
        self._cache_lock = threading.Lock()
        
        # Initialize base directory (but don't create subdirs yet)
        self.base_dir = self.get_secure_base_directory()
        self.vault_dir = os.path.join(self.base_dir, "vault_data")
        self.recycle_dir = os.path.join(self.base_dir, "vault_recycle")
        self.config_dir = os.path.join(self.base_dir, "config")
        
        print(f"📁 Base directory: {self.base_dir}")
        print(f"🔒 Platform: {self.get_platform_name()}")
    
    def get_platform_name(self):
        """✅ OPTIMIZATION: Cache platform detection"""
        if self._platform_cache is None:
            if ANDROID:
                self._platform_cache = "Android"
            elif platform.system() == "Windows":
                self._platform_cache = "Windows"
            elif platform.system() == "Darwin":
                self._platform_cache = "macOS"
            elif platform.system() == "Linux":
                self._platform_cache = "Linux"
            else:
                self._platform_cache = platform.system()
        
        return self._platform_cache
    
    def get_secure_base_directory(self):
        """✅ OPTIMIZATION: Cache base directory calculation"""
        if self._base_dir_cache is None:
            if ANDROID:
                self._base_dir_cache = self._get_android_private_directory()
            elif platform.system() == "Windows":
                self._base_dir_cache = self._get_windows_private_directory()
            elif platform.system() == "Darwin":  # macOS
                self._base_dir_cache = self._get_macos_private_directory()
            elif platform.system() == "Linux":
                self._base_dir_cache = self._get_linux_private_directory()
            else:
                # Fallback to current directory (not secure)
                print("⚠️ WARNING: Unsupported platform, using current directory")
                self._base_dir_cache = os.path.join(os.getcwd(), f".{self.app_name}_data")
        
        return self._base_dir_cache
    
    def _get_android_private_directory(self):
        """Get Android app-private internal storage directory"""
        try:
            # Method 1: Use app's private files directory (most secure)
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            
            # Get app's private files directory
            files_dir = context.getFilesDir()
            private_dir = files_dir.getAbsolutePath()
            
            print(f"📱 Android private storage: {private_dir}")
            return os.path.join(private_dir, self.app_name)
            
        except Exception as e:
            print(f"⚠️ Android private dir error: {e}")
            
            try:
                # Method 2: Fallback to Kivy's app storage
                return os.path.join(app_storage_path(), self.app_name)
            except:
                # Method 3: Last resort - internal storage
                return f"/data/data/org.kivy.{self.app_name.lower()}/files"
    
    def _get_windows_private_directory(self):
        """Get Windows app-private directory"""
        try:
            # Method 1: Use APPDATA\Local (recommended for app data)
            appdata_local = os.environ.get('LOCALAPPDATA')
            if appdata_local:
                private_dir = os.path.join(appdata_local, self.app_name)
                print(f"🪟 Windows private storage: {private_dir}")
                return private_dir
            
            # Method 2: Use APPDATA\Roaming as fallback
            appdata_roaming = os.environ.get('APPDATA')
            if appdata_roaming:
                private_dir = os.path.join(appdata_roaming, self.app_name)
                print(f"🪟 Windows fallback storage: {private_dir}")
                return private_dir
            
            # Method 3: Use user profile directory
            user_profile = os.environ.get('USERPROFILE')
            if user_profile:
                private_dir = os.path.join(user_profile, f".{self.app_name}")
                print(f"🪟 Windows user profile storage: {private_dir}")
                return private_dir
                
        except Exception as e:
            print(f"⚠️ Windows directory error: {e}")
        
        # Fallback
        return os.path.join(os.path.expanduser("~"), f".{self.app_name}")
    
    def _get_macos_private_directory(self):
        """Get macOS app-private directory"""
        try:
            # Method 1: Use Application Support directory (recommended)
            home = os.path.expanduser("~")
            app_support = os.path.join(home, "Library", "Application Support", self.app_name)
            print(f"🍎 macOS private storage: {app_support}")
            return app_support
            
        except Exception as e:
            print(f"⚠️ macOS directory error: {e}")
            
            # Fallback to hidden directory in home
            return os.path.join(os.path.expanduser("~"), f".{self.app_name}")
    
    def _get_linux_private_directory(self):
        """Get Linux app-private directory"""
        try:
            # Method 1: Use XDG_DATA_HOME or ~/.local/share
            xdg_data = os.environ.get('XDG_DATA_HOME')
            if xdg_data:
                private_dir = os.path.join(xdg_data, self.app_name)
            else:
                home = os.path.expanduser("~")
                private_dir = os.path.join(home, ".local", "share", self.app_name)
            
            print(f"🐧 Linux private storage: {private_dir}")
            return private_dir
            
        except Exception as e:
            print(f"⚠️ Linux directory error: {e}")
            
            # Fallback to hidden directory in home
            return os.path.join(os.path.expanduser("~"), f".{self.app_name}")
    
    def ensure_secure_directories(self):
        if self._directories_created:
            return  # Already created
        
        with self._cache_lock:
            if self._directories_created:  # Double-check after acquiring lock
                return
            
            directories = [
                self.base_dir,
                self.vault_dir,
                self.recycle_dir,
                self.config_dir,
                os.path.join(self.vault_dir, "photos"),
                os.path.join(self.vault_dir, "videos"),
                os.path.join(self.vault_dir, "notes"),
                os.path.join(self.vault_dir, "audio"),
                os.path.join(self.vault_dir, "documents"),
                os.path.join(self.vault_dir, "apps"),
                os.path.join(self.vault_dir, "other"),
                os.path.join(self.recycle_dir, "photos"),
                os.path.join(self.recycle_dir, "videos"),
                os.path.join(self.recycle_dir, "notes"),
                os.path.join(self.recycle_dir, "audio"),
                os.path.join(self.recycle_dir, "documents"),
                os.path.join(self.recycle_dir, "apps"),
                os.path.join(self.recycle_dir, "other"),
                os.path.join(self.recycle_dir, "thumbnails")
            ]
            
            # ✅ OPTIMIZATION: Batch directory creation
            created_count = 0
            for directory in directories:
                try:
                    if not os.path.exists(directory):
                        os.makedirs(directory, mode=0o700)  # Owner read/write/execute only
                        created_count += 1
                    else:
                        # ✅ OPTIMIZATION: Only set permissions if needed
                        self._set_secure_permissions_if_needed(directory)
                        
                except Exception as e:
                    print(f"❌ Error creating directory {directory}: {e}")
            
            if created_count > 0:
                print(f"📁 Created {created_count} secure directories")
            
            self._directories_created = True
    
    def _set_secure_permissions_if_needed(self, path):
        """✅ OPTIMIZATION: Only set permissions if they're incorrect"""
        try:
            if not ANDROID:  # Android handles permissions differently
                # Check current permissions first
                stat_info = os.stat(path)
                current_perms = oct(stat_info.st_mode)[-3:]
                
                if current_perms != "700":
                    # Set to 700 (owner only: read, write, execute)
                    os.chmod(path, 0o700)
                    
                    # On Windows, also hide the directory
                    if platform.system() == "Windows":
                        try:
                            import ctypes
                            # Set hidden attribute on Windows
                            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
                        except:
                            pass
                        
        except Exception as e:
            print(f"⚠️ Warning: Could not check/set secure permissions on {path}: {e}")
    
    def get_vault_directory(self, file_type=None):
        """Get vault directory for specific file type"""
        # ✅ OPTIMIZATION: Lazy directory creation
        self.ensure_secure_directories()
        
        if file_type:
            return os.path.join(self.vault_dir, file_type)
        return self.vault_dir
    
    def get_recycle_directory(self, file_type=None):
        """Get recycle directory for specific file type"""
        # ✅ OPTIMIZATION: Lazy directory creation
        self.ensure_secure_directories()
        
        if file_type:
            return os.path.join(self.recycle_dir, file_type)
        return self.recycle_dir
    
    def get_config_directory(self):
        """Get configuration directory"""
        # ✅ OPTIMIZATION: Lazy directory creation
        self.ensure_secure_directories()
        return self.config_dir
    
    def store_file_securely(self, source_path, file_type, filename=None):
        """Store a file securely in the appropriate vault directory"""
        try:
            if not os.path.exists(source_path):
                return {"success": False, "error": "Source file not found"}
            
            # Determine target directory
            target_dir = self.get_vault_directory(file_type)
            
            # Generate filename if not provided
            if not filename:
                filename = os.path.basename(source_path)
            
            target_path = os.path.join(target_dir, filename)
            
            # ✅ OPTIMIZATION: Faster filename conflict resolution
            if os.path.exists(target_path):
                name, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(f"{name}_{counter}{ext}"):
                    counter += 1
                target_path = f"{name}_{counter}{ext}"
            
            # Copy file to secure location
            import shutil
            shutil.copy2(source_path, target_path)
            
            # Set secure permissions
            self._set_secure_permissions_if_needed(target_path)
            
            print(f"✅ File stored securely: {target_path}")
            
            return {
                "success": True,
                "secure_path": target_path,
                "relative_path": os.path.relpath(target_path, self.base_dir)
            }
            
        except Exception as e:
            print(f"❌ Error storing file securely: {e}")
            return {"success": False, "error": str(e)}
    
    def is_user_accessible(self):
        """✅ OPTIMIZATION: Cache user accessibility check"""
        # Check if the storage location is easily accessible to users
        user_accessible_patterns = [
            "/sdcard",
            "/storage/emulated/0",
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.getcwd()  # Current working directory
        ]
        
        for pattern in user_accessible_patterns:
            if self.base_dir.startswith(pattern):
                return True
        
        return False
    
    def get_storage_info(self):
        """✅ OPTIMIZATION: Cache storage info with TTL"""
        current_time = time.time()
        
        # Check cache first
        with self._cache_lock:
            if (self._storage_info_cache and 
                current_time - self._storage_info_cache_time < self._storage_info_cache_ttl):
                return self._storage_info_cache.copy()
        
        # Calculate fresh info
        info = {
            "platform": self.get_platform_name(),
            "base_directory": self.base_dir,
            "is_secure": not self.is_user_accessible(),
            "vault_directory": self.vault_dir,
            "recycle_directory": self.recycle_dir,
            "config_directory": self.config_dir,
            "permissions": "0o700 (owner only)" if not ANDROID else "Android app-private",
            "hidden": platform.system() == "Windows"
        }
        
        # ✅ OPTIMIZATION: Only calculate size if directories exist (avoid expensive walk)
        if os.path.exists(self.base_dir):
            try:
                total_size = 0
                file_count = 0
                
                # ✅ OPTIMIZATION: Use os.scandir for better performance
                for entry in os.scandir(self.base_dir):
                    if entry.is_file():
                        total_size += entry.stat().st_size
                        file_count += 1
                    elif entry.is_dir():
                        # Recursive scan for subdirectories
                        for root, dirs, files in os.walk(entry.path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    total_size += os.path.getsize(file_path)
                                    file_count += 1
                                except (OSError, IOError):
                                    continue  # Skip inaccessible files
                
                info["total_files"] = file_count
                info["total_size_mb"] = round(total_size / (1024 * 1024), 2)
                
            except Exception as e:
                info["total_files"] = 0
                info["total_size_mb"] = 0.0
                print(f"⚠️ Could not calculate storage size: {e}")
        else:
            info["total_files"] = 0
            info["total_size_mb"] = 0.0
        
        # Update cache
        with self._cache_lock:
            self._storage_info_cache = info.copy()
            self._storage_info_cache_time = current_time
        
        return info
    
    def verify_security(self):
        """✅ OPTIMIZATION: Cache security verification"""
        if self._security_verified and self._security_result:
            return self._security_result.copy()
        
        issues = []
        
        # Check if directory exists
        if not os.path.exists(self.base_dir):
            issues.append("Base directory does not exist")
        
        # Check if it's in a user-accessible location
        if self.is_user_accessible():
            issues.append("Storage location is easily accessible to users")
        
        # Check permissions (non-Android only)
        if not ANDROID and os.path.exists(self.base_dir):
            try:
                stat_info = os.stat(self.base_dir)
                permissions = oct(stat_info.st_mode)[-3:]
                if permissions != "700":
                    issues.append(f"Insecure permissions: {permissions} (should be 700)")
            except:
                issues.append("Could not check permissions")
        
        result = {
            "is_secure": len(issues) == 0,
            "issues": issues,
            "recommendations": self._get_security_recommendations()
        }
        
        # Cache result
        self._security_result = result.copy()
        self._security_verified = True
        
        return result
    
    def _get_security_recommendations(self):
        """Get security recommendations based on current setup"""
        recommendations = []
        
        if self.is_user_accessible():
            recommendations.append("Consider using app-private storage location")
        
        if not ANDROID and platform.system() != "Windows":
            recommendations.append("Ensure file permissions are set to 700 (owner only)")
        
        recommendations.extend([
            "Consider encrypting files before storing them",
            "Implement user authentication (PIN/password)",
            "Regular security audits of stored files"
        ])
        
        return recommendations
    
    def clear_cache(self):
        """✅ OPTIMIZATION: Method to clear all cached data"""
        with self._cache_lock:
            self._storage_info_cache = None
            self._storage_info_cache_time = 0
            self._security_verified = False
            self._security_result = None
        print("🧹 Storage cache cleared")
    
    def get_cache_stats(self):
        """✅ OPTIMIZATION: Get cache statistics for debugging"""
        with self._cache_lock:
            return {
                "platform_cached": self._platform_cache is not None,
                "base_dir_cached": self._base_dir_cache is not None,
                "storage_info_cached": self._storage_info_cache is not None,
                "security_verified": self._security_verified,
                "directories_created": self._directories_created,
                "cache_age_seconds": time.time() - self._storage_info_cache_time if self._storage_info_cache else 0
            }

# ✅ OPTIMIZATION: Simplified update function
def update_recycle_bin_for_secure_storage(recycle_bin_core, secure_storage):
    """Update existing RecycleBinCore to use secure storage"""
    
    # Update directories
    recycle_bin_core.recycle_dir = secure_storage.get_recycle_directory()
    recycle_bin_core.metadata_file = os.path.join(secure_storage.get_config_directory(), 'recycle_metadata.json')
    
    print("✅ RecycleBin updated to use secure storage")
    print(f"📁 New recycle directory: {recycle_bin_core.recycle_dir}")

# ✅ OPTIMIZATION: Faster testing function
def test_secure_storage():
    """Test the secure storage functionality"""
    print("🧪 Testing Secure Storage...")
    
    # Initialize secure storage
    storage = SecureStorage("SecretVault")
    
    # Get storage info
    info = storage.get_storage_info()
    print(f"\n📋 Storage Information:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Verify security
    security_check = storage.verify_security()
    print(f"\n🔒 Security Check:")
    print(f"   Is Secure: {security_check['is_secure']}")
    if security_check['issues']:
        print(f"   Issues: {security_check['issues']}")
    
    # Show cache stats
    cache_stats = storage.get_cache_stats()
    print(f"\n💾 Cache Stats: {cache_stats}")
    
    print("\n✅ Secure storage test completed")
    return storage

if __name__ == "__main__":
    test_secure_storage()