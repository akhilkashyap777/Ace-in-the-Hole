# main_app.py - Main application with vault functionality + WebSocket game
import os
import threading
import subprocess
import sys
import asyncio
import json
import websockets
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Ellipse

# Vault imports
from photo_vault import integrate_photo_vault
from video_vault import integrate_video_vault
from recycle_bin_ui import integrate_recycle_bin
from secure_storage import SecureStorage
from vault_secure_integration import initialize_secure_vault
from document_vault import integrate_document_vault
from complete_contact_integration import setup_contact_system
from audio_vault_main_ui import integrate_audio_vault
from password_manager import PasswordManager
from password_ui import GamePasswordUI
from file_transfer_vault import integrate_file_transfer

# Try to import Android-specific modules
try:
    from android.permissions import request_permissions, Permission
    from plyer import notification
    ANDROID = True
except ImportError:
    ANDROID = False
    print("Not running on Android - volume buttons will use arrow keys")

class WebSocketGameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.websocket = None
        self.connected = False
        self.game_state = None
        self.server_url = "ws://69.62.78.126:8765"  # Replace with your VPS IP
        
        # Connection status
        self.connection_status = "Disconnected"
        
        # WebSocket thread and loop management
        self.ws_thread = None
        self.loop = None
        self.message_queue = []
        
        # Start connection
        self.connect_to_server()
        
        # Update display at 60 FPS
        Clock.schedule_interval(self.update_display, 1/60.0)
    
    def connect_to_server(self):
        """Connect to WebSocket server"""
        if self.ws_thread and self.ws_thread.is_alive():
            return
            
        self.ws_thread = threading.Thread(target=self._websocket_thread, daemon=True)
        self.ws_thread.start()
    
    def _websocket_thread(self):
        """WebSocket thread function"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self.websocket_handler())
        except Exception as e:
            print(f"WebSocket thread error: {e}")
        finally:
            self.loop.close()
    
    async def websocket_handler(self):
        """Handle WebSocket connection and messages"""
        try:
            self.connection_status = "Connecting..."
            async with websockets.connect(self.server_url) as websocket:
                self.websocket = websocket
                self.connected = True
                self.connection_status = "Connected ✅"
                print("✅ Connected to game server!")
                
                # Send any queued messages
                while self.message_queue:
                    message = self.message_queue.pop(0)
                    await self.send_message(message)
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data['type'] == 'game_state':
                            self.game_state = data
                    except json.JSONDecodeError:
                        print(f"Invalid JSON received: {message}")
                        
        except Exception as e:
            print(f"❌ Connection error: {e}")
            self.connected = False
            self.connection_status = "Connection Failed ❌"
    
    async def send_message(self, message):
        """Send message to server"""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(message))
                print(f"✉️ Message sent: {message}")
            except Exception as e:
                print(f"Error sending message: {e}")
    
    def send_message_sync(self, message):
        """Fixed synchronous wrapper for sending messages"""
        if self.loop and self.loop.is_running():
            # If loop exists and is running, schedule the coroutine
            future = asyncio.run_coroutine_threadsafe(
                self.send_message(message), 
                self.loop
            )
            try:
                # Wait for completion with timeout
                future.result(timeout=1.0)
            except Exception as e:
                print(f"Send message error: {e}")
        else:
            # Queue the message for later if no loop
            self.message_queue.append(message)
            print(f"📝 Message queued: {message}")
    
    def start_game(self):
        """Start the game"""
        if self.connected:
            self.send_message_sync({'type': 'start_game'})
            print("🎮 Starting game...")
        else:
            print("❌ Not connected to server - attempting to connect...")
            self.connect_to_server()
            # Queue the start message
            self.send_message_sync({'type': 'start_game'})
    
    def reset_game(self):
        """Reset the game"""
        if self.connected:
            self.send_message_sync({'type': 'reset_game'})
            print("🔄 Resetting game...")
        else:
            print("❌ Not connected to server")
    
    def update_display(self, dt):
        """Update the visual display based on game state"""
        if not self.game_state:
            return
        
        self.canvas.clear()
        
        with self.canvas:
            # Draw background
            self.draw_background()
            
            # Draw cards
            self.draw_cards()
    
    def draw_background(self):
        """Draw the game background"""
        if not self.game_state:
            return
        
        colors = self.game_state['colors']
        screen_w, screen_h = self.game_state['screen_size']
        
        # Scale to widget size
        scale_x = self.width / screen_w if screen_w > 0 else 1
        scale_y = self.height / screen_h if screen_h > 0 else 1
        
        # Felt background
        Color(colors['FELT_GREEN'][0]/255, colors['FELT_GREEN'][1]/255, colors['FELT_GREEN'][2]/255, 1)
        Rectangle(pos=self.pos, size=self.size)
        
        # Wood borders
        border_width = 30 * min(scale_x, scale_y)
        Color(colors['WOOD_BROWN'][0]/255, colors['WOOD_BROWN'][1]/255, colors['WOOD_BROWN'][2]/255, 1)
        
        # Top border
        Rectangle(pos=self.pos, size=(self.width, border_width))
        # Bottom border  
        Rectangle(pos=(self.x, self.y + self.height - border_width), size=(self.width, border_width))
        # Left border
        Rectangle(pos=self.pos, size=(border_width, self.height))
        # Right border
        Rectangle(pos=(self.x + self.width - border_width, self.y), size=(border_width, self.height))
        
        # Draw dots pattern
        Color(colors['DARK_GREEN'][0]/255, colors['DARK_GREEN'][1]/255, colors['DARK_GREEN'][2]/255, 1)
        dot_size = 2 * min(scale_x, scale_y)
        for y in range(int(50 * scale_y), int(self.height - 50 * scale_y), int(20 * scale_y)):
            for x in range(int(50 * scale_x), int(self.width - 50 * scale_x), int(40 * scale_x)):
                if (x + y) % int(80 * min(scale_x, scale_y)) == 0:
                    Ellipse(pos=(self.x + x - dot_size/2, self.y + y - dot_size/2), size=(dot_size, dot_size))
    
    def draw_cards(self):
        """Draw the cards based on game state"""
        if not self.game_state or 'cards' not in self.game_state:
            return
        
        colors = self.game_state['colors']
        screen_w, screen_h = self.game_state['screen_size']
        card_w, card_h = self.game_state['card_size']
        
        # Scale to widget size
        scale_x = self.width / screen_w if screen_w > 0 else 1
        scale_y = self.height / screen_h if screen_h > 0 else 1
        
        for card_data in self.game_state['cards']:
            # Calculate card position
            card_x = self.x + card_data['x'] * scale_x
            card_y = self.y + (screen_h - card_data['y'] - card_h) * scale_y  # Flip Y
            card_width = card_w * scale_x
            card_height = card_h * scale_y
            
            if card_data['is_face_up']:
                if card_data['is_winner']:
                    # Red Ace
                    Color(colors['RED'][0]/255, colors['RED'][1]/255, colors['RED'][2]/255, 1)
                    Rectangle(pos=(card_x, card_y), size=(card_width, card_height))
                    
                    # Black border
                    Color(colors['BLACK'][0]/255, colors['BLACK'][1]/255, colors['BLACK'][2]/255, 1)
                    border_w = 3 * min(scale_x, scale_y)
                    Rectangle(pos=(card_x, card_y + card_height - border_w), size=(card_width, border_w))  # top
                    Rectangle(pos=(card_x, card_y), size=(card_width, border_w))  # bottom
                    Rectangle(pos=(card_x, card_y), size=(border_w, card_height))  # left
                    Rectangle(pos=(card_x + card_width - border_w, card_y), size=(border_w, card_height))  # right
                else:
                    # Black card with "2"
                    Color(colors['BLACK'][0]/255, colors['BLACK'][1]/255, colors['BLACK'][2]/255, 1)
                    Rectangle(pos=(card_x, card_y), size=(card_width, card_height))
                    
                    # White border
                    Color(colors['WHITE'][0]/255, colors['WHITE'][1]/255, colors['WHITE'][2]/255, 1)
                    border_w = 3 * min(scale_x, scale_y)
                    Rectangle(pos=(card_x, card_y + card_height - border_w), size=(card_width, border_w))
                    Rectangle(pos=(card_x, card_y), size=(card_width, border_w))
                    Rectangle(pos=(card_x, card_y), size=(border_w, card_height))
                    Rectangle(pos=(card_x + card_width - border_w, card_y), size=(border_w, card_height))
            else:
                # Face down - blue with pattern
                Color(colors['BLUE'][0]/255, colors['BLUE'][1]/255, colors['BLUE'][2]/255, 1)
                Rectangle(pos=(card_x, card_y), size=(card_width, card_height))
                
                # Black border
                Color(colors['BLACK'][0]/255, colors['BLACK'][1]/255, colors['BLACK'][2]/255, 1)
                border_w = 3 * min(scale_x, scale_y)
                Rectangle(pos=(card_x, card_y + card_height - border_w), size=(card_width, border_w))
                Rectangle(pos=(card_x, card_y), size=(card_width, border_w))
                Rectangle(pos=(card_x, card_y), size=(border_w, card_height))
                Rectangle(pos=(card_x + card_width - border_w, card_y), size=(border_w, card_height))
                
                # White dots pattern
                Color(colors['WHITE'][0]/255, colors['WHITE'][1]/255, colors['WHITE'][2]/255, 1)
                dot_size = 8 * min(scale_x, scale_y)
                for i in range(3):
                    for j in range(4):
                        dot_x = card_x + 30 * scale_x + i * 30 * scale_x - dot_size/2
                        dot_y = card_y + 30 * scale_y + j * 25 * scale_y - dot_size/2
                        Ellipse(pos=(dot_x, dot_y), size=(dot_size, dot_size))
    
    def on_touch_down(self, touch):
        """Handle touch/click events"""
        if not self.connected or not self.game_state:
            return False
        
        if self.collide_point(*touch.pos):
            # Convert touch coordinates to game coordinates
            screen_w, screen_h = self.game_state['screen_size']
            scale_x = screen_w / self.width if self.width > 0 else 1
            scale_y = screen_h / self.height if self.height > 0 else 1
            
            relative_x = (touch.pos[0] - self.x) * scale_x
            relative_y = (screen_h - (touch.pos[1] - self.y) * scale_y)  # Flip Y
            
            # Send click to server
            self.send_message_sync({
                'type': 'click',
                'x': relative_x,
                'y': relative_y
            })
            return True
        return False


class VaultApp(MDApp):
    def __init__(self):
        super().__init__()
        self.volume_pattern = []
        self.target_pattern = ['up', 'down', 'up', 'down', 'up']
        self.vault_open = False
        self.current_screen = 'game'
        
        # Initialize password system
        self.password_manager = PasswordManager("SecretVault")
        self.password_ui = GamePasswordUI(self)
        
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        if ANDROID:
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        
        Window.bind(on_key_down=self.on_key_down)
        
        self.main_layout = MDBoxLayout(orientation='vertical')

        # Initialize vault systems (unchanged)
        self.secure_storage = SecureStorage("SecretVault")
        print(f"🔒 Secure storage: {self.secure_storage.get_storage_info()['base_directory']}")
        
        initialize_secure_vault(self)
        integrate_document_vault(self)
        setup_contact_system(self)
        integrate_audio_vault(self)
        integrate_photo_vault(self)
        integrate_video_vault(self)
        integrate_recycle_bin(self)
        integrate_file_transfer(self)
              
        # Create WebSocket game widget instead of local pygame
        self.game_widget = WebSocketGameWidget()
        self.main_layout.add_widget(self.game_widget)
        
        # Game info display
        self.create_game_ui()
        
        return self.main_layout
    
    def create_game_ui(self):
        """Create game UI elements"""
        # Game info panel
        info_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=5, padding=5)
        
        self.score_label = MDLabel(text="Score: 0", size_hint_x=0.15, font_style="Caption")
        self.streak_label = MDLabel(text="Streak: 0", size_hint_x=0.15, font_style="Caption") 
        self.round_label = MDLabel(text="Round: 1", size_hint_x=0.15, font_style="Caption")
        self.speed_label = MDLabel(text="Speed: 0.3x", size_hint_x=0.15, font_style="Caption")
        self.status_label = MDLabel(text="Connecting...", size_hint_x=0.4, font_style="Caption")
        
        info_layout.add_widget(self.score_label)
        info_layout.add_widget(self.streak_label)
        info_layout.add_widget(self.round_label)
        info_layout.add_widget(self.speed_label)
        info_layout.add_widget(self.status_label)
        
        self.main_layout.add_widget(info_layout)
        
        # Instruction label
        self.instruction_label = MDLabel(
            text="Connecting to server...", 
            size_hint_y=None, 
            height='30dp',
            halign="center",
            font_style="Body2"
        )
        self.main_layout.add_widget(self.instruction_label)
        
        # Control buttons
        button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=10, padding=10)
        
        start_btn = MDRaisedButton(text='Start Game', size_hint_x=0.5)
        start_btn.bind(on_press=self.start_game)
        button_layout.add_widget(start_btn)
        
        reset_btn = MDRaisedButton(text='Reset Game', size_hint_x=0.5)
        reset_btn.bind(on_press=self.reset_game)
        button_layout.add_widget(reset_btn)
        
        self.main_layout.add_widget(button_layout)
        
        # Update UI periodically
        Clock.schedule_interval(self.update_game_ui, 1/10.0)  # 10 FPS for UI updates
    
    def update_game_ui(self, dt):
        """Update game UI labels based on WebSocket game state"""
        if hasattr(self, 'game_widget') and self.game_widget.game_state:
            state = self.game_widget.game_state
            
            self.score_label.text = f"Score: {state['score']}"
            self.streak_label.text = f"Streak: {state['streak']}"
            self.round_label.text = f"Round: {state['round_num']}"
            self.speed_label.text = f"Speed: {state['shuffle_speed']:.2f}x"
            self.instruction_label.text = state.get('instruction', '')
            
        # Update connection status
        if hasattr(self, 'game_widget'):
            self.status_label.text = self.game_widget.connection_status
    
    def on_key_down(self, window, key, scancode, codepoint, modifier):
        """Volume button pattern detection for vault access (unchanged)"""
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
                self.request_vault_access()
            
            return True
        
        return False
    
    def request_vault_access(self):
        """Handle vault access request - shows password prompt (unchanged)"""
        if self.password_manager.is_first_launch():
            self.password_ui.show_first_setup()
        else:
            self.password_ui.show_password_prompt()
    
    def start_game(self, instance):
        """Start the WebSocket game"""
        print("🎮 Starting WebSocket game...")
        self.game_widget.start_game()
    
    def reset_game(self, instance):
        """Reset the WebSocket game completely"""
        print("🔄 Resetting WebSocket game...")
        self.game_widget.reset_game()
    
    def create_vault_card(self, icon, title, subtitle, callback):
        """Create a beautiful card for vault sections (unchanged)"""
        card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height="120dp",
            size_hint_x=1,
            padding="15dp",
            spacing="8dp",
            elevation=4,
            radius=[8, 8, 8, 8],
            md_bg_color=self.theme_cls.primary_color,
            ripple_behavior=True
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
            text_size=(None, None),
            valign="middle"
        )
        text_layout.add_widget(title_label)
        
        subtitle_label = MDLabel(
            text=subtitle,
            font_style="Body2",
            theme_text_color="Custom",
            text_color="white",
            opacity=0.9,
            size_hint_y=None,
            height="25dp",
            text_size=(None, None),
            valign="middle"
        )
        text_layout.add_widget(subtitle_label)
        
        content_layout.add_widget(text_layout)
        card.add_widget(content_layout)
        
        # Make entire card clickable
        card.bind(on_release=callback)
        
        return card
    
    def open_vault(self):
        """Show the actual vault interface after successful authentication (unchanged)"""
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
            padding=["20dp", "10dp", "20dp", "20dp"]
        )
        
        # Vault cards grid with proper spacing
        cards_layout = MDBoxLayout(
            orientation='vertical', 
            spacing="12dp",
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

        transfer_card = self.create_vault_card(
            "wifi",
            "File Transfer",
            "Share files via WiFi",
            lambda x: self.show_file_transfer()
        )
        cards_layout.add_widget(transfer_card)
        
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
        """Return to main vault screen from photo gallery (unchanged)"""
        self.open_vault()
    
    def back_to_game(self, instance):
        """Return to game from vault (unchanged)"""
        self.vault_open = False
        self.volume_pattern = []
        self.current_screen = 'game'
        
        # Rebuild the main interface
        self.main_layout.clear_widgets()
        
        # Recreate WebSocket game widget and UI
        self.game_widget = WebSocketGameWidget()
        self.main_layout.add_widget(self.game_widget)
        
        self.create_game_ui()

if __name__ == '__main__':
    VaultApp().run()