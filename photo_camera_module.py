# photo_camera_module.py - Photo Camera Integration
"""
Photo Camera Module for Secret Vault App

This module adds camera functionality specifically to the photo vault.
Simply import and attach to your PhotoGalleryWidget.

Usage in photo_vault_ui.py:
    from photo_camera_module import PhotoCameraModule
    
    # In PhotoGalleryWidget.__init__():
    self.camera_module = PhotoCameraModule(self)
    
    # In PhotoGalleryWidget.build_header():
    camera_buttons = self.camera_module.build_camera_buttons()
    header.add_widget(camera_buttons)
"""

import os
import shutil
import tempfile
from datetime import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp

# Android imports
try:
    from android.permissions import request_permissions, Permission
    from android.storage import app_storage_path
    from plyer import camera
    from jnius import autoclass, cast
    ANDROID = True
except ImportError:
    ANDROID = False

class PhotoCameraModule:
    """
    Photo Camera Module - Handles camera capture for photo vault
    """
    
    def __init__(self, photo_gallery_widget):
        self.gallery_widget = photo_gallery_widget
        self.vault_core = photo_gallery_widget.vault_core
        self.processing = False
    
    def build_camera_buttons(self):
        """Build camera buttons for photo capture"""
        if not ANDROID:
            return self.build_desktop_message()
        
        # Android camera buttons
        camera_container = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            padding=10,
            spacing=15,
            elevation=3,
            md_bg_color=[0.2, 0.3, 0.4, 0.9]  # Dark BlueGray
        )
        
        # Camera label
        camera_label = MDLabel(
            text='📸 CAMERA',
            font_style="Subtitle1",
            text_color="white",
            size_hint_x=0.3,
            halign="center",
            bold=True
        )
        camera_container.add_widget(camera_label)
        
        # Front camera button
        front_btn = MDRaisedButton(
            text='🤳 Front',
            md_bg_color=[0.3, 0.6, 0.9, 1],  # Blue
            text_color="white",
            size_hint_x=0.35,
            elevation=4
        )
        front_btn.bind(on_press=lambda x: self.take_photo('front'))
        camera_container.add_widget(front_btn)
        
        # Back camera button
        back_btn = MDRaisedButton(
            text='📷 Back',
            md_bg_color=[0.2, 0.7, 0.3, 1],  # Green
            text_color="white",
            size_hint_x=0.35,
            elevation=4
        )
        back_btn.bind(on_press=lambda x: self.take_photo('back'))
        camera_container.add_widget(back_btn)
        
        return camera_container
    
    def build_desktop_message(self):
        """Build message for desktop users"""
        message_container = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=15,
            spacing=10,
            elevation=2,
            md_bg_color=[0.4, 0.4, 0.4, 0.7]
        )
        
        message_label = MDLabel(
            text='📱 Photo capture is only available on Android devices',
            font_style="Body2",
            text_color=[0.9, 0.9, 0.9, 1],
            halign="center"
        )
        message_container.add_widget(message_label)
        return message_container
    
    def take_photo(self, camera_type):
        """Take photo with specified camera"""
        if not ANDROID or self.processing:
            return
        
        try:
            self.processing = True
            
            # Request permissions
            request_permissions([
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
            
            # Show starting message
            self.show_popup(f'📱 Opening {camera_type} camera for photo...', 'Camera Starting', 2)
            
            # Get temp file path
            temp_path = self.get_temp_photo_path()
            if not temp_path:
                self.processing = False
                return
            
            # Launch camera with intent
            self.launch_camera_intent(camera_type, temp_path)
            
        except Exception as e:
            print(f"❌ Error taking photo: {e}")
            self.processing = False
    
    def get_temp_photo_path(self):
        """Get temporary path for photo capture"""
        try:
            cache_dir = os.path.join(app_storage_path(), 'camera_cache')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"temp_photo_{timestamp}.jpg"
            return os.path.join(cache_dir, filename)
        except Exception as e:
            print(f"❌ Error creating temp path: {e}")
            return None
    
    def launch_camera_intent(self, camera_type, temp_path):
        """Launch Android camera with intent"""
        try:
            # Get Android classes
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            # Create camera intent
            intent = Intent('android.media.action.IMAGE_CAPTURE')
            
            # Set camera preference (front=1, back=0)
            camera_facing = 1 if camera_type == 'front' else 0
            intent.putExtra('android.intent.extras.CAMERA_FACING', camera_facing)
            
            # Set output file
            output_file = File(temp_path)
            output_uri = Uri.fromFile(output_file)
            intent.putExtra('output', output_uri)
            
            # Launch camera
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivityForResult(intent, 100)  # Photo request code
            
            print(f"📱 Launched {camera_type} camera for photo")
            
            # Start checking for completion
            self.schedule_photo_completion_check(temp_path)
            
        except Exception as e:
            print(f"❌ Camera intent error: {e}")
            self.processing = False
    
    def schedule_photo_completion_check(self, temp_path):
        """Schedule periodic checks for photo completion"""
        self.check_count = 0
        
        def check_photo_complete(dt):
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                print(f"✅ Photo capture completed: {temp_path}")
                self.on_photo_captured(temp_path)
            else:
                self.check_count += 1
                if self.check_count < 60:  # Check for 30 seconds
                    Clock.schedule_once(check_photo_complete, 0.5)
                else:
                    print("⏰ Photo capture timeout - assuming cancelled")
                    self.processing = False
        
        Clock.schedule_once(check_photo_complete, 1.0)
    
    def on_photo_captured(self, temp_path):
        """Handle photo capture completion"""
        try:
            # Move photo to vault
            success = self.move_photo_to_vault(temp_path)
            
            if success:
                self.show_popup('✅ Photo saved to secure vault!', 'Photo Captured', 3)
                # Refresh gallery
                Clock.schedule_once(lambda dt: self.gallery_widget.refresh_gallery(None), 1.0)
            else:
                self.show_popup('❌ Failed to save photo to vault', 'Error', 3)
            
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error processing photo: {e}")
        finally:
            self.processing = False
    
    def move_photo_to_vault(self, temp_path):
        """Move captured photo to photo vault"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"vault_{timestamp}_camera_photo.jpg"
            
            # Get vault directory
            vault_dir = self.vault_core.get_vault_directory()
            destination = os.path.join(vault_dir, filename)
            
            # Ensure vault directory exists
            if not os.path.exists(vault_dir):
                os.makedirs(vault_dir)
            
            # Move file to vault
            shutil.move(temp_path, destination)
            print(f"📸 Photo moved to vault: {destination}")
            
            # Verify it's a valid image
            if hasattr(self.vault_core, 'is_image_file'):
                if not self.vault_core.is_image_file(destination):
                    print("⚠️ Warning: Captured file may not be a valid image")
            
            return True
            
        except Exception as e:
            print(f"❌ Error moving photo to vault: {e}")
            return False
    
    def show_popup(self, message, title, duration=3):
        """Show popup message"""
        content = MDLabel(
            text=message,
            text_color="white",
            halign='center',
            font_style="Body1"
        )
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.5),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), duration)