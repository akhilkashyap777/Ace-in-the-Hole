# game_widget.py - Kivy widget that displays the pygame game
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color
import pygame
from monte_game import MonteGame

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.texture = None
        Clock.schedule_interval(self.update_game, 1/60.0)
        
    def start_game(self):
        self.game = MonteGame((int(self.width), int(self.height)))
        self.game.show_cards()
        
    def update_game(self, dt):
        if self.game:
            self.game.update()
            self.game.draw()
            
            # Convert pygame surface to kivy texture
            w, h = self.game.get_surface().get_size()
            raw = pygame.image.tostring(self.game.get_surface(), 'RGB')
            
            from kivy.graphics.texture import Texture
            self.texture = Texture.create(size=(w, h))
            self.texture.blit_buffer(raw, colorfmt='rgb', bufferfmt='ubyte')
            self.texture.flip_vertical()
            
            self.canvas.clear()
            with self.canvas:
                Color(1, 1, 1, 1)
                Rectangle(texture=self.texture, pos=self.pos, size=self.size)
    
    def on_touch_down(self, touch):
        if self.game and self.collide_point(*touch.pos):
            # Convert kivy coordinates to pygame coordinates
            relative_x = touch.pos[0] - self.pos[0]
            relative_y = self.size[1] - (touch.pos[1] - self.pos[1])  # Flip Y coordinate
            pygame_pos = (relative_x, relative_y)
            self.game.handle_click(pygame_pos)
            return True
        return False