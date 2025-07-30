from photo_vault_core import PhotoVaultCore
from photo_vault_ui import PhotoGalleryWidget

# Main PhotoVault class that combines core and UI
class PhotoVault:
    """
    Main Photo Vault class that combines core functionality with UI
    """
    def __init__(self, app_instance):
        self.core = PhotoVaultCore(app_instance)
        self.app = app_instance
    
    def create_photo_gallery_widget(self):
        """Create the main photo gallery widget"""
        return PhotoGalleryWidget(self.core)
    
    # Expose core methods for backward compatibility
    def get_vault_directory(self):
        return self.core.get_vault_directory()
    
    def request_permissions(self):
        return self.core.request_permissions()
    
    def select_photos_from_gallery(self, callback):
        return self.core.select_photos_from_gallery(callback)
    
    def get_vault_photos(self):
        return self.core.get_vault_photos()
    
    def delete_photo(self, photo_path):
        return self.core.delete_photo(photo_path)
    
    def export_photo(self, photo_path, user_selected_folder=None):
        return self.core.export_photo(photo_path, user_selected_folder)
    
    def is_image_file(self, file_path):
        return self.core.is_image_file(file_path)

# Integration helper function
def integrate_photo_vault(vault_app):
    """Helper function to integrate photo vault into the main app"""
    vault_app.photo_vault = PhotoVault(vault_app)
    
    def show_photo_gallery():
        """Show the photo gallery"""
        vault_app.main_layout.clear_widgets()
        
        # Create photo gallery widget
        photo_gallery = vault_app.photo_vault.create_photo_gallery_widget()
        vault_app.main_layout.add_widget(photo_gallery)
        
        # Store reference for navigation
        vault_app.current_screen = 'photo_gallery'
    
    # Add method to vault app
    vault_app.show_photo_gallery = show_photo_gallery
    
    return vault_app.photo_vault

# Re-export main classes for backwards compatibility
__all__ = [
    'PhotoVault',
    'PhotoVaultCore', 
    'PhotoGalleryWidget',
    'integrate_photo_vault'
]

# Platform detection for logging
try:
    from android.storage import app_storage_path
    PLATFORM = "Android"
except ImportError:
    import platform
    PLATFORM = platform.system()
    
DEBUG_MODE = True

# Quick integration test function
def test_photo_vault_integration():
    """
    Test function to verify photo vault can be integrated
    Run this to check if all dependencies are available
    """
    try:
        class MockApp:
            pass
        
        mock_app = MockApp()
        mock_app.secure_storage = None  # Will use fallback
        
        core = PhotoVaultCore(mock_app)
        
        test_files = [
            "photo.jpg", "image.png", "graphic.gif", "picture.bmp",
            "modern.webp", "scan.tiff", "icon.svg", "phone.heic",
            "document.pdf", "music.mp3", "video.mp4"  # Non-images
        ]
        
        return True
        
    except Exception as e:
        return False

if __name__ == "__main__":
    test_photo_vault_integration()