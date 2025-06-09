# main_app.py - Main application with vault functionality
import os
import threading
import subprocess
import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from game_widget import GameWidget
from photo_vault import integrate_photo_vault
from video_vault import integrate_video_vault
from recycle_bin_ui import integrate_recycle_bin
from secure_storage import SecureStorage
from vault_secure_integration import initialize_secure_vault
from document_vault import integrate_document_vault
from complete_contact_integration import setup_contact_system
from audio_vault_ui import integrate_audio_vault

# Try to import Android-specific modules
try:
    from android.permissions import request_permissions, Permission
    from plyer import notification
    ANDROID = True
except ImportError:
    ANDROID = False
    print("Not running on Android - volume buttons will use arrow keys")

class VaultApp(App):
    def __init__(self):
        super().__init__()
        self.volume_pattern = []
        self.target_pattern = ['up', 'down', 'up', 'down', 'up']
        self.vault_open = False
        self.current_screen = 'game'
        
    def build(self):
        if ANDROID:
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        
        Window.bind(on_key_down=self.on_key_down)
        
        self.main_layout = BoxLayout(orientation='vertical')

        self.secure_storage = SecureStorage("SecretVault")
        print(f"🔒 Secure storage: {self.secure_storage.get_storage_info()['base_directory']}")
        
        initialize_secure_vault(self) # Your existing line
        integrate_document_vault(self)
        setup_contact_system(self)
        integrate_audio_vault(self)
        integrate_photo_vault(self)
        integrate_video_vault(self)
        integrate_recycle_bin(self)
              
        self.game_widget = GameWidget()
        self.main_layout.add_widget(self.game_widget)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10, padding=10)
        
        start_btn = Button(text='Start Game', font_size=18)
        start_btn.bind(on_press=self.start_game)
        button_layout.add_widget(start_btn)
        
        reset_btn = Button(text='Reset', font_size=18)
        reset_btn.bind(on_press=self.reset_game)
        button_layout.add_widget(reset_btn)
        
        self.main_layout.add_widget(button_layout)
        
        # Status label
        self.status_label = Label(
            text='Status: Ready | Secret: ↑↓↑↓↑ to open vault',
            font_size=14,
            size_hint_y=0.05
        )
        self.main_layout.add_widget(self.status_label)
        
        return self.main_layout
    
    def on_key_down(self, window, key, scancode, codepoint, modifier):
        key_map = {
            24: 'up',    # Volume Up on Android
            25: 'down',  # Volume Down on Android
            273: 'up',   # Up arrow for desktop testing
            274: 'down'  # Down arrow for desktop testing
        }
        
        if key in key_map:
            button = key_map[key]
            self.volume_pattern.append(button)
            
            if len(self.volume_pattern) > 5:
                self.volume_pattern.pop(0)
            
            # Update status based on current screen
            if self.current_screen == 'game':
                self.status_label.text = f'Pattern: {" ".join(self.volume_pattern)} | Target: ↑↓↑↓↑'
            
            if self.volume_pattern == self.target_pattern:
                self.open_vault()
            
            return True
        
        return False
    
    def start_game(self, instance):
        self.game_widget.start_game()
        if self.current_screen == 'game':
            self.status_label.text = 'Status: Game Running | Secret: ↑↓↑↓↑ to open vault'
    
    def reset_game(self, instance):
        if self.game_widget.game:
            self.game_widget.game.reset_game()
            self.game_widget.game.show_cards()
    
    def open_vault(self):
        self.vault_open = True
        self.current_screen = 'vault_main'

        self.main_layout.clear_widgets()
        
        vault_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(
            text='🔓 SECRET VAULT OPENED! 🔓',
            font_size=32,
            size_hint_y=0.15
        )
        vault_layout.add_widget(title)
        
        # Main vault content with buttons
        content_layout = BoxLayout(orientation='vertical', spacing=15)
        
        # Photo vault button - EXISTING
        photo_btn = Button(
            text='📁 Hidden Photos (Click to manage)',
            font_size=20,
            size_hint_y=None,
            height=60
        )
        photo_btn.bind(on_press=lambda x: self.show_photo_gallery())
        content_layout.add_widget(photo_btn)

        # Video vault button - EXISTING
        video_btn = Button(
            text='🎬 Hidden Videos (Click to manage)',
            font_size=20,
            size_hint_y=None,
            height=60
        )
        video_btn.bind(on_press=lambda x: self.show_video_gallery())
        content_layout.add_widget(video_btn)

        document_btn = Button(
            text='📁 Documents (Click to manage)',
            font_size=20,
            size_hint_y=None,
            height=60
        )
        document_btn.bind(on_press=lambda x: self.show_document_vault())
        content_layout.add_widget(document_btn)

        audio_btn = Button(
            text='🎵 Audio Files',
            font_size=20,
            size_hint_y=None,
            height=60
        )
        audio_btn.bind(on_press=lambda x: self.show_audio_vault())
        content_layout.add_widget(audio_btn)
        
        # NEW: Recycle bin button - ADD THIS ENTIRE SECTION
        recycle_btn = Button(
            text='🗑️ Recycle Bin (Restore deleted files)',
            font_size=20,
            size_hint_y=None,
            height=60,
            background_color=(0.8, 0.6, 0.2, 1)  # Orange color to stand out
        )
        recycle_btn.bind(on_press=lambda x: self.show_recycle_bin())
        content_layout.add_widget(recycle_btn)
        
        # Other vault sections (existing) - KEEP AS IS
        other_content = Label(
            text='''📝 Secure Notes (7 notes)  
    🔐 Password Manager (15 accounts)
    📄 Private Documents (12 files)
    💰 Financial Records (5 files)

    [These features coming soon...]
            ''',
            font_size=16,
            text_size=(None, None),
            halign='center'
        )
        content_layout.add_widget(other_content)
        
        vault_layout.add_widget(content_layout)
        
        # Back button - EXISTING
        back_btn = Button(text='Back to Game', font_size=18, size_hint_y=0.1)
        back_btn.bind(on_press=self.back_to_game)
        vault_layout.add_widget(back_btn)
        
        self.main_layout.add_widget(vault_layout)
        
        # Status label - EXISTING
        self.status_label = Label(
            text='Status: VAULT OPEN - Your files are secure',
            font_size=14,
            size_hint_y=0.05
        )
        self.main_layout.add_widget(self.status_label)
        
        if ANDROID:
            try:
                notification.notify(
                    title='Vault Opened',
                    message='Secret vault has been unlocked',
                    timeout=2
                )
            except:
                pass
    
    def show_vault_main(self):
        """Return to main vault screen from photo gallery"""
        self.open_vault()
    
    def back_to_game(self, instance):
        self.vault_open = False
        self.volume_pattern = []
        self.current_screen = 'game'
        
        # Rebuild the main interface
        self.main_layout.clear_widgets()
        
        self.game_widget = GameWidget()
        self.main_layout.add_widget(self.game_widget)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10, padding=10)
        
        start_btn = Button(text='Start Game', font_size=18)
        start_btn.bind(on_press=self.start_game)
        button_layout.add_widget(start_btn)
        
        reset_btn = Button(text='Reset', font_size=18)
        reset_btn.bind(on_press=self.reset_game)
        button_layout.add_widget(reset_btn)
        
        self.main_layout.add_widget(button_layout)
        
        self.status_label = Label(
            text='Status: Ready | Secret: ↑↓↑↓↑ to open vault',
            font_size=14,
            size_hint_y=0.05
        )
        self.main_layout.add_widget(self.status_label)

if __name__ == '__main__':
    VaultApp().run()