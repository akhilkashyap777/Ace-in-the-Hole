# monte_game.py - Fixed version with correct pygame Surface syntax
import pygame
import random

class MonteGame:
    def __init__(self, surface_size=(800, 600)):
        pygame.init()
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = surface_size
        self.CARD_WIDTH = 120
        self.CARD_HEIGHT = 160
        self.CARD_SPACING = 50
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GOLD = (255, 215, 0)
        self.DARK_GREEN = (0, 100, 50)
        self.FELT_GREEN = (53, 101, 77)
        self.WOOD_BROWN = (139, 69, 19)
        self.LIGHT_BROWN = (205, 133, 63)
        
        # FIX: Use correct pygame Surface syntax
        self.screen = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        
        # ✅ OPTIMIZATION: Pre-create and cache all fonts
        self._font_cache = {
            'small': pygame.font.Font(None, 36),
            'large': pygame.font.Font(None, 72),
            'card_ace': pygame.font.Font(None, 72),
            'card_number': pygame.font.Font(None, 48)
        }
        
        # ✅ OPTIMIZATION: Cache static background
        self._background_cache = None
        self._background_dirty = True
        
        # ✅ OPTIMIZATION: Frame skipping for performance
        self._last_draw_state = None
        self._draw_dirty = True
        
        # ✅ OPTIMIZATION: Text rendering cache
        self._text_cache = {}
        self._text_cache_max_size = 50
        
        self.reset_game()
        self.running = True
        
    def reset_game(self):
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.round_num = 1
        self.game_state = "showing"
        self.shuffle_speed = 0.3
        self.shuffle_count = 0
        self.max_shuffles = 6
        self.show_timer = 0
        self.result_timer = 0
        self.last_guess_correct = True
        
        # ✅ OPTIMIZATION: Mark as dirty for redraw
        self._draw_dirty = True
        self._background_dirty = True
        
        # Create cards
        card_y = self.SCREEN_HEIGHT // 2 - self.CARD_HEIGHT // 2
        start_x = self.SCREEN_WIDTH // 2 - (3 * self.CARD_WIDTH + 2 * self.CARD_SPACING) // 2
        
        self.cards = []
        winner_pos = random.randint(0, 2)
        
        for i in range(3):
            card_x = start_x + i * (self.CARD_WIDTH + self.CARD_SPACING)
            is_winner = (i == winner_pos)
            card = Card(card_x, card_y, is_winner, self)
            self.cards.append(card)
    
    def _get_cached_text(self, text, font_name, color):
        """✅ OPTIMIZATION: Cache rendered text to avoid recreation"""
        cache_key = (text, font_name, color)
        
        if cache_key in self._text_cache:
            return self._text_cache[cache_key]
        
        # Clean cache if too large
        if len(self._text_cache) >= self._text_cache_max_size:
            # Remove oldest entries (simple FIFO)
            old_keys = list(self._text_cache.keys())[:10]
            for key in old_keys:
                del self._text_cache[key]
        
        # Render and cache
        font = self._font_cache.get(font_name, self._font_cache['small'])
        rendered_text = font.render(text, True, color)
        self._text_cache[cache_key] = rendered_text
        
        return rendered_text
    
    def _get_current_state_hash(self):
        """✅ OPTIMIZATION: Generate hash of current visual state for dirty checking"""
        state_data = (
            self.game_state,
            self.score,
            self.streak,
            self.best_streak,
            self.round_num,
            self.shuffle_speed,
            tuple((card.x, card.y, card.is_face_up, card.moving) for card in self.cards)
        )
        return hash(state_data)
    
    def show_cards(self):
        for card in self.cards:
            card.is_face_up = True
        self.show_timer = pygame.time.get_ticks()
        self._draw_dirty = True  # ✅ Mark for redraw
    
    def hide_cards(self):
        for card in self.cards:
            card.is_face_up = False
        self._draw_dirty = True  # ✅ Mark for redraw
    
    def shuffle_cards(self):
        if self.shuffle_count < self.max_shuffles:
            card1, card2 = random.sample(self.cards, 2)
            temp_x, temp_y = card1.target_x, card1.target_y
            card1.move_to(card2.target_x, card2.target_y)
            card2.move_to(temp_x, temp_y)
            self.shuffle_count += 1
            self._draw_dirty = True  # ✅ Mark for redraw
        else:
            all_still = all(not card.moving for card in self.cards)
            if all_still:
                self.game_state = "guessing"
                self._draw_dirty = True
    
    def handle_click(self, pos):
        if self.game_state == "guessing":
            for i, card in enumerate(self.cards):
                if card.rect.collidepoint(pos):
                    self.show_cards()
                    self.game_state = "result"
                    self.result_timer = pygame.time.get_ticks()
                    
                    if card.is_winner:
                        self.score += 10
                        self.streak += 1
                        self.best_streak = max(self.best_streak, self.streak)
                        self.last_guess_correct = True
                    else:
                        self.streak = 0
                        self.shuffle_speed = 0.3
                        self.max_shuffles = 6
                        self.last_guess_correct = False
                    
                    self._draw_dirty = True  # ✅ Mark for redraw
                    return
        elif self.game_state == "result":
            self.next_round()
    
    def next_round(self):
        self.round_num += 1
        
        if self.last_guess_correct:
            self.shuffle_speed += 0.05 + (self.streak * 0.01)
            self.max_shuffles = min(12, 6 + (self.streak // 3))
        
        self.shuffle_count = 0
        self.game_state = "showing"
        
        card_y = self.SCREEN_HEIGHT // 2 - self.CARD_HEIGHT // 2
        start_x = self.SCREEN_WIDTH // 2 - (3 * self.CARD_WIDTH + 2 * self.CARD_SPACING) // 2
        
        self.cards = []
        winner_pos = random.randint(0, 2)
        
        for i in range(3):
            card_x = start_x + i * (self.CARD_WIDTH + self.CARD_SPACING)
            is_winner = (i == winner_pos)
            card = Card(card_x, card_y, is_winner, self)
            self.cards.append(card)
        
        self.show_cards()
        self._draw_dirty = True  # ✅ Mark for redraw
    
    def update(self):
        if not self.running:
            return
        
        # ✅ OPTIMIZATION: Track if any visual changes occurred
        cards_changed = False
        
        if self.game_state == "showing":
            if pygame.time.get_ticks() - self.show_timer > 2000:
                self.hide_cards()
                self.game_state = "shuffling"
                self._draw_dirty = True
        
        elif self.game_state == "shuffling":
            current_time = pygame.time.get_ticks()
            shuffle_interval = max(200, int(800 / self.shuffle_speed))
            
            if not hasattr(self, 'last_shuffle_time'):
                self.last_shuffle_time = current_time
            
            if current_time - self.last_shuffle_time > shuffle_interval:
                self.shuffle_cards()
                self.last_shuffle_time = current_time
                cards_changed = True
        
        elif self.game_state == "result":
            if pygame.time.get_ticks() - self.result_timer > 2000:
                self.next_round()
        
        # ✅ OPTIMIZATION: Check if cards moved (for animation)
        for card in self.cards:
            if card.update_position():
                cards_changed = True
        
        if cards_changed:
            self._draw_dirty = True
    
    def _draw_background_cached(self):
        """✅ OPTIMIZATION: Draw and cache static background"""
        if self._background_cache is None or self._background_dirty:
            # Create background surface - FIX: Use correct syntax here too
            self._background_cache = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            surface = self._background_cache
            
            surface.fill(self.FELT_GREEN)
            
            border_width = 30
            pygame.draw.rect(surface, self.WOOD_BROWN, (0, 0, self.SCREEN_WIDTH, border_width))
            pygame.draw.rect(surface, self.WOOD_BROWN, (0, self.SCREEN_HEIGHT - border_width, self.SCREEN_WIDTH, border_width))
            pygame.draw.rect(surface, self.WOOD_BROWN, (0, 0, border_width, self.SCREEN_HEIGHT))
            pygame.draw.rect(surface, self.WOOD_BROWN, (self.SCREEN_WIDTH - border_width, 0, border_width, self.SCREEN_HEIGHT))
            
            trim_width = 5
            pygame.draw.rect(surface, self.LIGHT_BROWN, (trim_width, trim_width, self.SCREEN_WIDTH - 2*trim_width, border_width - trim_width))
            pygame.draw.rect(surface, self.LIGHT_BROWN, (trim_width, self.SCREEN_HEIGHT - border_width, self.SCREEN_WIDTH - 2*trim_width, border_width - trim_width))
            pygame.draw.rect(surface, self.LIGHT_BROWN, (trim_width, trim_width, border_width - trim_width, self.SCREEN_HEIGHT - 2*trim_width))
            pygame.draw.rect(surface, self.LIGHT_BROWN, (self.SCREEN_WIDTH - border_width, trim_width, border_width - trim_width, self.SCREEN_HEIGHT - 2*trim_width))
            
            # ✅ OPTIMIZATION: Simplified pattern (fewer draw calls)
            for y in range(50, self.SCREEN_HEIGHT - 50, 40):
                for x in range(50, self.SCREEN_WIDTH - 50, 80):
                    pygame.draw.circle(surface, self.DARK_GREEN, (x, y), 1)
            
            self._background_dirty = False
        
        # Blit cached background
        self.screen.blit(self._background_cache, (0, 0))
    
    def draw(self):
        # ✅ OPTIMIZATION: Skip drawing if nothing changed
        current_state = self._get_current_state_hash()
        if current_state == self._last_draw_state and not self._draw_dirty:
            return  # Skip redraw
        
        self._draw_background_cached()
        
        # Draw cards
        for card in self.cards:
            card.draw(self.screen)
        
        # ✅ OPTIMIZATION: Use cached text rendering
        score_text = self._get_cached_text(f"Score: {self.score}", 'small', self.WHITE)
        streak_text = self._get_cached_text(f"Streak: {self.streak}", 'small', self.GOLD if self.streak > 0 else self.WHITE)
        best_streak_text = self._get_cached_text(f"Best: {self.best_streak}", 'small', self.GOLD)
        round_text = self._get_cached_text(f"Round: {self.round_num}", 'small', self.WHITE)
        speed_text = self._get_cached_text(f"Speed: {self.shuffle_speed:.2f}x", 'small', self.WHITE)
        
        # ✅ OPTIMIZATION: Single background rectangle for UI
        pygame.draw.rect(self.screen, self.BLACK, (5, 5, 200, 140))
        
        self.screen.blit(score_text, (15, 15))
        self.screen.blit(streak_text, (15, 45))
        self.screen.blit(best_streak_text, (15, 75))
        self.screen.blit(round_text, (15, 105))
        self.screen.blit(speed_text, (15, 135))
        
        # Draw instructions
        if self.game_state == "showing":
            instruction = "Remember the RED ACE!"
        elif self.game_state == "shuffling":
            instruction = "Follow the cards..."
        elif self.game_state == "guessing":
            instruction = "Click the card with the RED ACE!"
        elif self.game_state == "result":
            if self.last_guess_correct:
                instruction = f"CORRECT! +10 points | Streak: {self.streak} (Click to continue)"
            else:
                instruction = f"WRONG! Streak broken! Speed reset (Click to continue)"
        
        instruction_text = self._get_cached_text(instruction, 'small', self.WHITE)
        instruction_rect = instruction_text.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT - 50))
        
        pygame.draw.rect(self.screen, self.BLACK, instruction_rect.inflate(30, 15))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Draw title
        title_text = self._get_cached_text("3 CARD MONTE", 'large', self.GOLD)
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH//2, 50))
        pygame.draw.rect(self.screen, self.BLACK, title_rect.inflate(30, 15))
        self.screen.blit(title_text, title_rect)
        
        # ✅ OPTIMIZATION: Update state tracking
        self._last_draw_state = current_state
        self._draw_dirty = False
    
    def get_surface(self):
        return self.screen
    
    def cleanup(self):
        """✅ OPTIMIZATION: Proper cleanup method"""
        self._text_cache.clear()
        self._background_cache = None
        if hasattr(self, 'cards'):
            self.cards.clear()

class Card:
    def __init__(self, x, y, is_winner, game):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.is_winner = is_winner
        self.is_face_up = False
        self.rect = pygame.Rect(x, y, game.CARD_WIDTH, game.CARD_HEIGHT)
        self.moving = False
        self.game = game
        
        # ✅ OPTIMIZATION: Pre-render card faces to avoid recreation
        self._face_cache = {}
        self._render_faces()
        
    def _render_faces(self):
        """✅ OPTIMIZATION: Pre-render all card faces"""
        # Winner face (Red Ace) - FIX: Use correct syntax
        winner_surface = pygame.Surface((self.game.CARD_WIDTH, self.game.CARD_HEIGHT), pygame.SRCALPHA)
        winner_surface.fill(self.game.RED)
        pygame.draw.rect(winner_surface, self.game.BLACK, (0, 0, self.game.CARD_WIDTH, self.game.CARD_HEIGHT), 3)
        
        ace_text = self.game._font_cache['card_ace'].render("A", True, self.game.WHITE)
        ace_rect = ace_text.get_rect(center=(self.game.CARD_WIDTH//2, self.game.CARD_HEIGHT//2))
        winner_surface.blit(ace_text, ace_rect)
        self._face_cache['winner'] = winner_surface
        
        # Loser face (Black 2) - FIX: Use correct syntax
        loser_surface = pygame.Surface((self.game.CARD_WIDTH, self.game.CARD_HEIGHT), pygame.SRCALPHA)
        loser_surface.fill(self.game.BLACK)
        pygame.draw.rect(loser_surface, self.game.WHITE, (0, 0, self.game.CARD_WIDTH, self.game.CARD_HEIGHT), 3)
        
        two_text = self.game._font_cache['card_number'].render("2", True, self.game.WHITE)
        two_rect = two_text.get_rect(center=(self.game.CARD_WIDTH//2, self.game.CARD_HEIGHT//2))
        loser_surface.blit(two_text, two_rect)
        self._face_cache['loser'] = loser_surface
        
        # Back face - FIX: Use correct syntax
        back_surface = pygame.Surface((self.game.CARD_WIDTH, self.game.CARD_HEIGHT), pygame.SRCALPHA)
        back_surface.fill(self.game.BLUE)
        pygame.draw.rect(back_surface, self.game.BLACK, (0, 0, self.game.CARD_WIDTH, self.game.CARD_HEIGHT), 3)
        
        # ✅ OPTIMIZATION: Simplified back pattern
        for i in range(0, 3):
            for j in range(0, 4):
                pygame.draw.circle(back_surface, self.game.WHITE, 
                                 (30 + i * 30, 30 + j * 25), 8)
        self._face_cache['back'] = back_surface
    
    def update_position(self):
        """✅ OPTIMIZATION: Return True if position changed"""
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            if abs(dx) > 1 or abs(dy) > 1:
                self.x += dx * 0.15
                self.y += dy * 0.15
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                return True
            else:
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                return True
        return False
        
    def draw(self, screen):
        """✅ OPTIMIZATION: Use pre-rendered surfaces"""
        # Select appropriate face
        if self.is_face_up:
            face_key = 'winner' if self.is_winner else 'loser'
        else:
            face_key = 'back'
        
        # Blit pre-rendered surface
        screen.blit(self._face_cache[face_key], (int(self.x), int(self.y)))
    
    def move_to(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.moving = True
