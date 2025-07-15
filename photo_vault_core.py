import os
import shutil
import threading
import re
import mimetypes
from datetime import datetime
from kivy.clock import Clock
from PIL import Image as PILImage

# Cross-platform imports
try:
    from android.permissions import request_permissions, Permission
    from plyer import filechooser
    from android.storage import primary_external_storage_path, app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False
    import tkinter as tk
    from tkinter import filedialog

class PhotoVaultCore:
    """
    Photo Vault Core - Handles secure photo storage and operations
    
    Features:
    - Universal image format detection (MIME + PIL verification)
    - Cross-platform file operations
    - Export functionality with folder selection
    - Recycle bin integration
    """
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.vault_dir = self.get_vault_directory()
        self.ensure_vault_directory()
        self.processing = False  # Flag to prevent multiple operations
        
        # Initialize MIME types for better detection
        mimetypes.init()
        
    def get_vault_directory(self):
        """Get the secure directory for storing vault photos"""
        if hasattr(self.app, 'secure_storage'):
            return self.app.secure_storage.get_vault_directory('photos')
        
        # Cross-platform fallback
        if ANDROID:
            try:
                return os.path.join(app_storage_path(), 'vault_photos')
            except:
                return os.path.join('/sdcard', 'vault_photos')
        else:
            return os.path.join(os.getcwd(), 'vault_photos')
    
    def ensure_vault_directory(self):
        """Create vault directory if it doesn't exist"""
        try:
            if not os.path.exists(self.vault_dir):
                os.makedirs(self.vault_dir)
        except Exception as e:
            print(f"Error creating vault directory: {e}")
    
    def is_image_file(self, file_path):
        """Detect if file is an image using MIME type and PIL verification"""
        try:
            # First check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith('image/'):
                # Verify it's actually openable as image
                with PILImage.open(file_path) as img:
                    img.verify()
                return True
        except:
            pass
        return False
    
    def request_permissions(self):
        """Request necessary permissions for file access"""
        if ANDROID:
            try:
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Permission error: {e}")
    
    def select_photos_from_gallery(self, callback):
        """Open gallery/file picker to select photos"""
        if self.processing:
            return
            
        self.processing = True
        
        if ANDROID:
            self.android_file_picker(callback)
        else:
            self.desktop_file_picker(callback)
    
    def android_file_picker(self, callback):
        """Android file picker using plyer"""
        try:
            def on_selection(selection):
                Clock.schedule_once(lambda dt: self.handle_selection_async(selection, callback), 0)
            
            filechooser.open_file(
                on_selection=on_selection,
                multiple=True,
                filters=['*.*']  # Accept all files, filter with is_image_file()
            )
        except Exception as e:
            print(f"Error opening Android file chooser: {e}")
            self.processing = False
            self.fallback_file_picker(callback)
    
    def desktop_file_picker(self, callback):
        """Desktop file picker using tkinter"""
        def pick_files():
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                file_paths = filedialog.askopenfilenames(
                    title="Select Photos",
                    filetypes=[
                        ("All Image files", "*.*"),  # Let system detect
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self.handle_selection_async(file_paths, callback), 0)
                
            except Exception as e:
                print(f"Desktop file picker error: {e}")
                self.processing = False
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=pick_files)
        thread.daemon = True
        thread.start()
    
    def fallback_file_picker(self, callback):
        """Fallback file picker using Kivy's FileChooser"""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.popup import Popup
        from kivy.uix.filechooser import FileChooserIconView
        from kivy.metrics import dp
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # File chooser
        if ANDROID:
            try:
                start_path = primary_external_storage_path()
            except:
                start_path = '/sdcard'
        else:
            start_path = os.path.expanduser('~')
        
        filechooser = FileChooserIconView(
            path=start_path,
            filters=['*.*'],  # Accept all, filter later
            multiselect=True
        )
        content.add_widget(filechooser)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        select_btn = Button(text='Select Photos', size_hint_x=0.5)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        
        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Select Photos from Gallery',
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        
        def on_select(instance):
            if filechooser.selection:
                popup.dismiss()
                Clock.schedule_once(lambda dt: self.handle_selection_async(filechooser.selection, callback), 0.1)
            else:
                popup.dismiss()
                self.processing = False
        
        def on_cancel(instance):
            popup.dismiss()
            self.processing = False
        
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=on_cancel)
        
        popup.open()
    
    def handle_selection_async(self, file_paths, callback):
        """Handle selected photo files asynchronously"""
        if not file_paths:
            self.processing = False
            return
        
        def process_files():
            try:
                imported_files = []
                skipped_files = []
                
                for file_path in file_paths:
                    try:
                        # Check if it's actually an image
                        if not self.is_image_file(file_path):
                            skipped_files.append(f"{os.path.basename(file_path)} (not an image)")
                            continue
                        
                        # Keep original filename with conflict resolution
                        original_filename = os.path.basename(file_path)
                        destination = os.path.join(self.vault_dir, original_filename)
                        
                        # Handle filename conflicts
                        counter = 1
                        while os.path.exists(destination):
                            name_part, ext_part = os.path.splitext(original_filename)
                            new_filename = f"{name_part} ({counter}){ext_part}"
                            destination = os.path.join(self.vault_dir, new_filename)
                            counter += 1
                        
                        # Copy file to vault directory
                        shutil.copy2(file_path, destination)
                        imported_files.append(destination)
                        
                    except Exception as e:
                        print(f"Error copying file {file_path}: {e}")
                        skipped_files.append(f"{os.path.basename(file_path)} (error)")
                
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self.finish_import(imported_files, skipped_files, callback), 0)
                
            except Exception as e:
                print(f"Error processing files: {e}")
                Clock.schedule_once(lambda dt: self.finish_import([], [], callback), 0)
        
        # Run file operations in background thread
        thread = threading.Thread(target=process_files)
        thread.daemon = True
        thread.start()
        
        # Run file operations in background thread
        thread = threading.Thread(target=process_files)
        thread.daemon = True
        thread.start()
    
    def finish_import(self, imported_files, skipped_files, callback):
        """Finish import process on main thread"""
        self.processing = False
        callback(imported_files, skipped_files)
    
    def get_vault_photos(self):
        """Get list of all photos in vault using universal image detection"""
        photos = []
        try:
            if os.path.exists(self.vault_dir):
                for filename in os.listdir(self.vault_dir):
                    file_path = os.path.join(self.vault_dir, filename)
                    if os.path.isfile(file_path) and self.is_image_file(file_path):
                        photos.append(file_path)
            return sorted(photos, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
        except Exception as e:
            print(f"Error getting vault photos: {e}")
            return []
    
    def delete_photo(self, photo_path):
        """Move photo to recycle bin instead of permanent deletion"""
        try:
            if hasattr(self.app, 'recycle_bin'):
                result = self.app.recycle_bin.move_to_recycle(
                    file_path=photo_path,
                    original_location=os.path.dirname(photo_path),
                    metadata={
                        'vault_type': 'photos',
                        'original_name': os.path.basename(photo_path)
                    }
                )
                
                if result['success']:
                    return True
                else:
                    return False
            else:
                # Fallback to permanent deletion if recycle bin not available
                print("⚠️ Recycle bin not available, using permanent deletion")
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Error moving photo to recycle bin: {e}")
            return False
    
    def export_photo(self, photo_path, user_selected_folder=None):
        """Export photo to user-selected location"""
        try:
            if not os.path.exists(photo_path):
                return {'success': False, 'error': 'Photo not found'}
            
            # Use the actual filename (no more vault prefix removal needed)
            original_name = os.path.basename(photo_path)
            
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
            shutil.copy2(photo_path, export_path)
            
            return {
                'success': True,
                'export_path': export_path,
                'original_name': original_name,
                'export_folder': user_selected_folder
            }
            
        except Exception as e:
            print(f"Error exporting photo: {e}")
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
                fallback_folder = os.path.join(app_storage_path(), 'exported_photos')
            else:
                fallback_folder = os.path.join(os.path.expanduser('~'), 'Pictures')
            
            if not os.path.exists(fallback_folder):
                os.makedirs(fallback_folder)
            
            callback({'success': True, 'folder_path': fallback_folder, 'is_fallback': True})
            
        except Exception as e:
            callback({'success': False, 'error': f'Fallback folder creation failed: {e}'})