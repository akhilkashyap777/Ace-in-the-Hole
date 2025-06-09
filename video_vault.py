# video_vault.py - Main video vault file that imports core and UI components
"""
Video Vault for the Secret Vault App

This file combines the core video vault functionality with the UI components.
Split into separate files for better organization and easier debugging:

- video_vault_core.py: Core functionality (file operations, thumbnail generation, deletion)
- video_vault_ui.py: User interface components (gallery widget, file selection dialogs)

The main issue we're solving is Windows file locking when trying to delete videos.
This happens because OpenCV's VideoCapture objects don't release file handles properly.

Key fixes implemented:
1. Comprehensive tracking of all OpenCV VideoCapture objects
2. Immediate and explicit release of all captures after use
3. Multiple deletion methods with fallbacks
4. Process killing for stubborn file locks
5. Aggressive cleanup with garbage collection
6. Detailed logging to track what's happening

Usage:
- Import and use integrate_video_vault(app) in your main app
- The vault will handle video import, thumbnail generation, and secure deletion
- Videos can be moved (more secure) or copied to the vault
- Supports both Android and desktop platforms
"""

# Import all the functionality from the separate files
from video_vault_core import VideoVaultCore, ANDROID, OPENCV_AVAILABLE
from video_vault_ui import VideoVault, VideoGalleryWidget, integrate_video_vault

# Re-export the main classes and functions for backwards compatibility
__all__ = [
    'VideoVault',
    'VideoVaultCore', 
    'VideoGalleryWidget',
    'integrate_video_vault',
    'ANDROID',
    'OPENCV_AVAILABLE'
]

# You can also import specific components if needed:
# from video_vault_core import VideoVaultCore
# from video_vault_ui import VideoGalleryWidget

print("Video Vault module loaded successfully")
print(f"Platform: {'Android' if ANDROID else 'Desktop'}")
print(f"OpenCV available: {OPENCV_AVAILABLE}")

# For debugging, you can enable verbose logging by setting this to True
DEBUG_MODE = True

if DEBUG_MODE:
    print("🔧 DEBUG MODE ENABLED - Verbose logging active")
    print("📁 Video files will be stored in: vault_videos/")
    print("🖼️ Thumbnails will be stored in: vault_videos/thumbnails/")
    print("🗑️ Enhanced deletion methods enabled for Windows file locking issues")