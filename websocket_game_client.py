# websocket_game_client.py - Updated game_widget and main components for WebSocket

import asyncio
import json
import threading
import websockets
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Ellipse
from kivy.graphics.instructions import InstructionGroup
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton

class WebSocketGameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.websocket = None
        self.connected = False
        self.game_state = None
        self.server_url = "ws://69.62.78.126:8765"  # Replace with your VPS IP
        
        # Visual elements
        self.cards_graphics = []
        self.background_graphics = None
        self.ui_graphics = None
        
        # Start connection
        self.connect_to_server()
        
        # Update display at 60 FPS
        Clock.schedule_interval(self.update_display, 1/60.0)
    
    def connect_to_server(self):
        """Connect to WebSocket server"""
        def run_async():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.websocket_handler())
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    async def websocket_handler(self):
        """Handle WebSocket connection and messages"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                self.websocket = websocket
                self.connected = True
                print("✅ Connected to game server!")
                
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
    
    async def send_message(self, message):
        """Send message to server"""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")
    
    def send_message_sync(self, message):
        """Synchronous wrapper for sending messages"""
        if self.connected:
            asyncio.create_task(self.send_message(message))
    
    def start_game(self):
        """Start the game"""
        self.send_message_sync({'type': 'start_game'})
    
    def reset_game(self):
        """Reset the game"""
        self.send_message_sync({'type': 'reset_game'})
    
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
            
            # Draw UI elements
            self.draw_ui()
    
    def draw_background(self):
        """Draw the game background"""
        if not self.game_state:
            return
        
        colors = self.game_state['colors']
        screen_w, screen_h = self.game_state['screen_size']
        
        # Scale to widget size
        scale_x = self.width / screen_w
        scale_y = self.height / screen_h
        
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
        
        # Light trim
        trim_width = 5 * min(scale_x, scale_y)
        Color(colors['LIGHT_BROWN'][0]/255, colors['LIGHT_BROWN'][1]/255, colors['LIGHT_BROWN'][2]/255, 1)
        
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
        scale_x = self.width / screen_w
        scale_y = self.height / screen_h
        
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
                    # Draw border (top, bottom, left, right)
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
    
    def draw_ui(self):
        """Draw UI elements (will be handled by labels in main app)"""
        pass
    
    def on_touch_down(self, touch):
        """Handle touch/click events"""
        if not self.connected or not self.game_state:
            return False
        
        if self.collide_point(*touch.pos):
            # Convert touch coordinates to game coordinates
            screen_w, screen_h = self.game_state['screen_size']
            scale_x = screen_w / self.width
            scale_y = screen_h / self.height
            
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


class WebSocketGameApp(MDApp):
    def __init__(self):
        super().__init__()
        
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Game widget
        self.game_widget = WebSocketGameWidget()
        main_layout.add_widget(self.game_widget)
        
        # UI info labels
        info_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=10, padding=10)
        
        self.score_label = MDLabel(text="Score: 0", size_hint_x=0.2)
        self.streak_label = MDLabel(text="Streak: 0", size_hint_x=0.2) 
        self.round_label = MDLabel(text="Round: 1", size_hint_x=0.2)
        self.speed_label = MDLabel(text="Speed: 0.3x", size_hint_x=0.2)
        self.status_label = MDLabel(text="Connecting...", size_hint_x=0.2)
        
        info_layout.add_widget(self.score_label)
        info_layout.add_widget(self.streak_label)
        info_layout.add_widget(self.round_label)
        info_layout.add_widget(self.speed_label)
        info_layout.add_widget(self.status_label)
        
        main_layout.add_widget(info_layout)
        
        # Instruction label
        self.instruction_label = MDLabel(
            text="Connecting to server...", 
            size_hint_y=None, 
            height='40dp',
            halign="center"
        )
        main_layout.add_widget(self.instruction_label)
        
        # Control buttons
        button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=10, padding=10)
        
        start_btn = MDRaisedButton(text='Start Game', size_hint_x=0.5)
        start_btn.bind(on_press=self.start_game)
        button_layout.add_widget(start_btn)
        
        reset_btn = MDRaisedButton(text='Reset', size_hint_x=0.5)
        reset_btn.bind(on_press=self.reset_game)
        button_layout.add_widget(reset_btn)
        
        main_layout.add_widget(button_layout)
        
        # Update UI periodically
        Clock.schedule_interval(self.update_ui, 1/10.0)  # 10 FPS for UI updates
        
        return main_layout
    
    def update_ui(self, dt):
        """Update UI labels based on game state"""
        if self.game_widget.game_state:
            state = self.game_widget.game_state
            
            self.score_label.text = f"Score: {state['score']}"
            self.streak_label.text = f"Streak: {state['streak']}"
            self.round_label.text = f"Round: {state['round_num']}"
            self.speed_label.text = f"Speed: {state['shuffle_speed']:.2f}x"
            self.instruction_label.text = state.get('instruction', '')
            
            if self.game_widget.connected:
                self.status_label.text = "Connected ✅"
            else:
                self.status_label.text = "Disconnected ❌"
        else:
            if self.game_widget.connected:
                self.status_label.text = "Connected ✅"
            else:
                self.status_label.text = "Connecting..."
    
    def start_game(self, instance):
        self.game_widget.start_game()
    
    def reset_game(self, instance):
        self.game_widget.reset_game()

if __name__ == '__main__':
    WebSocketGameApp().run()