# main_app.py - Main application with vault functionality
import os
import threading
import subprocess
import sys
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
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

class VaultApp(MDApp):
    def __init__(self):
        super().__init__()
        self.volume_pattern = []
        self.target_pattern = ['up', 'down', 'up', 'down', 'up']
        self.vault_open = False
        self.current_screen = 'game'
        
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        if ANDROID:
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        
        Window.bind(on_key_down=self.on_key_down)
        
        self.main_layout = MDBoxLayout(orientation='vertical')

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
        button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10, padding=10)
        
        start_btn = MDRaisedButton(text='Start Game', size_hint_x=0.5)
        start_btn.bind(on_press=self.start_game)
        button_layout.add_widget(start_btn)
        
        reset_btn = MDRaisedButton(text='Reset', size_hint_x=0.5)
        reset_btn.bind(on_press=self.reset_game)
        button_layout.add_widget(reset_btn)
        
        self.main_layout.add_widget(button_layout)
        
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
            
            if self.volume_pattern == self.target_pattern:
                self.open_vault()
            
            return True
        
        return False
    
    def start_game(self, instance):
        self.game_widget.start_game()
    
    def reset_game(self, instance):
        if self.game_widget.game:
            self.game_widget.game.reset_game()
            self.game_widget.game.show_cards()
    
    def create_vault_card(self, icon, title, subtitle, callback):
        """Create a beautiful card for vault sections with proper sizing and rectangular shape"""
        card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height="120dp",  # Increased height to accommodate content
            size_hint_x=1,   # Full width
            padding="15dp",  # Increased padding
            spacing="8dp",
            elevation=4,
            radius=[8, 8, 8, 8],  # Reduced radius for more rectangular look
            md_bg_color=self.theme_cls.primary_color,
            ripple_behavior=True  # Add ripple effect for better UX
        )
        
        content_layout = MDBoxLayout(
            orientation='horizontal', 
            spacing="20dp",
            size_hint_y=1,
            adaptive_height=True
        )
        
        # Icon container with fixed size
        icon_container = MDBoxLayout(
            size_hint_x=None,
            width="60dp",
            orientation='vertical',
            pos_hint={'center_y': 0.5}
        )
        
        icon_btn = MDIconButton(
            icon=icon,
            theme_icon_color="Custom",
            icon_color="white",
            icon_size="45dp",
            size_hint=(None, None),
            size=("60dp", "60dp"),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        icon_btn.bind(on_press=callback)
        icon_container.add_widget(icon_btn)
        content_layout.add_widget(icon_container)
        
        # Text content with proper sizing
        text_layout = MDBoxLayout(
            orientation='vertical', 
            spacing="5dp",
            size_hint_x=1,
            adaptive_height=True,
            pos_hint={'center_y': 0.5}
        )
        
        title_label = MDLabel(
            text=title,
            font_style="H6",
            theme_text_color="Custom",
            text_color="white",
            size_hint_y=None,
            height="35dp",
            text_size=(None, None),  # Allow text to size naturally
            valign="middle"
        )
        text_layout.add_widget(title_label)
        
        subtitle_label = MDLabel(
            text=subtitle,
            font_style="Body2",  # Changed from Caption for better visibility
            theme_text_color="Custom",
            text_color="white",
            opacity=0.9,  # Slightly less transparent
            size_hint_y=None,
            height="25dp",
            text_size=(None, None),  # Allow text to size naturally
            valign="middle"
        )
        text_layout.add_widget(subtitle_label)
        
        content_layout.add_widget(text_layout)
        card.add_widget(content_layout)
        
        # Make entire card clickable
        card.bind(on_release=callback)
        
        return card
    
    def open_vault(self):
        self.vault_open = True
        self.current_screen = 'vault_main'

        self.main_layout.clear_widgets()
        
        # Main container
        main_container = MDBoxLayout(orientation='vertical')
        
        # Title (fixed at top)
        title = MDLabel(
            text='High Roller Suite',
            font_style="H4",
            halign="center",
            size_hint_y=None,
            height="60dp",
            theme_text_color="Primary"
        )
        main_container.add_widget(title)
        
        # Scrollable content
        scroll_view = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width="4dp",
            bar_color=self.theme_cls.primary_color,
            bar_inactive_color=self.theme_cls.primary_color,
            effect_cls="ScrollEffect",
            scroll_type=['bars', 'content']
        )
        
        # Scrollable content container
        scroll_content = MDBoxLayout(
            orientation='vertical',
            spacing="15dp",
            size_hint_y=None,
            adaptive_height=True,
            padding=["20dp", "10dp", "20dp", "20dp"]  # left, top, right, bottom
        )
        
        # Vault cards grid with proper spacing
        cards_layout = MDBoxLayout(
            orientation='vertical', 
            spacing="12dp",  # Consistent spacing
            size_hint_y=None,
            adaptive_height=True
        )
        
        # Photo vault card
        photo_card = self.create_vault_card(
            "image-multiple",
            "Hidden Photos",
            "Secure photo storage",
            lambda x: self.show_photo_gallery()
        )
        cards_layout.add_widget(photo_card)

        # Video vault card
        video_card = self.create_vault_card(
            "video",
            "Hidden Videos", 
            "Private video collection",
            lambda x: self.show_video_gallery()
        )
        cards_layout.add_widget(video_card)

        # Document vault card
        document_card = self.create_vault_card(
            "file-document",
            "Documents",
            "Important files & papers",
            lambda x: self.show_document_vault()
        )
        cards_layout.add_widget(document_card)

        # Audio vault card
        audio_card = self.create_vault_card(
            "music",
            "Audio Files",
            "Private audio recordings",
            lambda x: self.show_audio_vault()
        )
        cards_layout.add_widget(audio_card)
        
        # Recycle bin card
        recycle_card = self.create_vault_card(
            "delete",
            "Recycle Bin",
            "Restore deleted files",
            lambda x: self.show_recycle_bin()
        )
        cards_layout.add_widget(recycle_card)
        
        # Add cards to scroll content
        scroll_content.add_widget(cards_layout)
        
        # Back button (inside scroll area)
        back_btn = MDRaisedButton(
            text='Back to Game',
            size_hint_y=None,
            height="50dp",
            size_hint_x=None,
            width="200dp",
            pos_hint={'center_x': 0.5}
        )
        back_btn.bind(on_press=self.back_to_game)
        scroll_content.add_widget(back_btn)
        
        # Add some extra spacing at bottom
        bottom_spacer = MDLabel(
            text="",
            size_hint_y=None,
            height="20dp"
        )
        scroll_content.add_widget(bottom_spacer)
        
        # Add scroll content to scroll view
        scroll_view.add_widget(scroll_content)
        main_container.add_widget(scroll_view)
        
        self.main_layout.add_widget(main_container)
        
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
        
        button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10, padding=10)
        
        start_btn = MDRaisedButton(text='Start Game', size_hint_x=0.5)
        start_btn.bind(on_press=self.start_game)
        button_layout.add_widget(start_btn)
        
        reset_btn = MDRaisedButton(text='Reset', size_hint_x=0.5)
        reset_btn.bind(on_press=self.reset_game)
        button_layout.add_widget(reset_btn)
        
        self.main_layout.add_widget(button_layout)

if __name__ == '__main__':
    VaultApp().run()
