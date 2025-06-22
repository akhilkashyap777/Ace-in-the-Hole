# monte_game.py - Fixed version with separated movement logic
import pygame
import random
import time
import math

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
        
        self.screen = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
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
    
    def show_cards(self):
        for card in self.cards:
            card.is_face_up = True
        self.show_timer = pygame.time.get_ticks()
    
    def hide_cards(self):
        for card in self.cards:
            card.is_face_up = False
    
    def shuffle_cards(self):
        if self.shuffle_count < self.max_shuffles:
            card1, card2 = random.sample(self.cards, 2)
            temp_x, temp_y = card1.target_x, card1.target_y
            card1.move_to(card2.target_x, card2.target_y)
            card2.move_to(temp_x, temp_y)
            self.shuffle_count += 1
        else:
            # Check if all cards have finished moving
            all_still = all(not card.moving for card in self.cards)
            if all_still:
                self.game_state = "guessing"
    
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
    
    def update(self):
        if not self.running:
            return
        
        # Update card movements FIRST - this is crucial!
        for card in self.cards:
            card.update_movement()
            
        if self.game_state == "showing":
            if pygame.time.get_ticks() - self.show_timer > 2000:
                self.hide_cards()
                self.game_state = "shuffling"
        
        elif self.game_state == "shuffling":
            current_time = pygame.time.get_ticks()
            shuffle_interval = max(200, int(800 / self.shuffle_speed))
            
            if not hasattr(self, 'last_shuffle_time'):
                self.last_shuffle_time = current_time
            
            if current_time - self.last_shuffle_time > shuffle_interval:
                self.shuffle_cards()
                self.last_shuffle_time = current_time
        
        elif self.game_state == "result":
            if pygame.time.get_ticks() - self.result_timer > 2000:
                self.next_round()
    
    def draw_background(self):
        self.screen.fill(self.FELT_GREEN)
        
        border_width = 30
        pygame.draw.rect(self.screen, self.WOOD_BROWN, (0, 0, self.SCREEN_WIDTH, border_width))
        pygame.draw.rect(self.screen, self.WOOD_BROWN, (0, self.SCREEN_HEIGHT - border_width, self.SCREEN_WIDTH, border_width))
        pygame.draw.rect(self.screen, self.WOOD_BROWN, (0, 0, border_width, self.SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, self.WOOD_BROWN, (self.SCREEN_WIDTH - border_width, 0, border_width, self.SCREEN_HEIGHT))
        
        trim_width = 5
        pygame.draw.rect(self.screen, self.LIGHT_BROWN, (trim_width, trim_width, self.SCREEN_WIDTH - 2*trim_width, border_width - trim_width))
        pygame.draw.rect(self.screen, self.LIGHT_BROWN, (trim_width, self.SCREEN_HEIGHT - border_width, self.SCREEN_WIDTH - 2*trim_width, border_width - trim_width))
        pygame.draw.rect(self.screen, self.LIGHT_BROWN, (trim_width, trim_width, border_width - trim_width, self.SCREEN_HEIGHT - 2*trim_width))
        pygame.draw.rect(self.screen, self.LIGHT_BROWN, (self.SCREEN_WIDTH - border_width, trim_width, border_width - trim_width, self.SCREEN_HEIGHT - 2*trim_width))
        
        for y in range(50, self.SCREEN_HEIGHT - 50, 20):
            for x in range(50, self.SCREEN_WIDTH - 50, 40):
                if (x + y) % 80 == 0:
                    pygame.draw.circle(self.screen, self.DARK_GREEN, (x, y), 1)
    
    def draw(self):
        self.draw_background()
        
        for card in self.cards:
            card.draw(self.screen)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        streak_text = self.font.render(f"Streak: {self.streak}", True, self.GOLD if self.streak > 0 else self.WHITE)
        best_streak_text = self.font.render(f"Best: {self.best_streak}", True, self.GOLD)
        round_text = self.font.render(f"Round: {self.round_num}", True, self.WHITE)
        speed_text = self.font.render(f"Speed: {self.shuffle_speed:.2f}x", True, self.WHITE)
        
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
        
        instruction_text = self.font.render(instruction, True, self.WHITE)
        instruction_rect = instruction_text.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT - 50))
        
        pygame.draw.rect(self.screen, self.BLACK, instruction_rect.inflate(30, 15))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Draw title
        title_text = self.big_font.render("3 CARD MONTE", True, self.GOLD)
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH//2, 50))
        pygame.draw.rect(self.screen, self.BLACK, title_rect.inflate(30, 15))
        self.screen.blit(title_text, title_rect)
    
    def get_surface(self):
        return self.screen

class Card:
    def __init__(self, x, y, is_winner, game):
        self.x = float(x)  # Use float for smoother movement
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.is_winner = is_winner
        self.is_face_up = False
        self.rect = pygame.Rect(int(x), int(y), game.CARD_WIDTH, game.CARD_HEIGHT)
        self.moving = False
        self.game = game
        self.movement_speed = 0.15  # Movement interpolation speed
        
    def update_movement(self):
        """Update card movement - separated from drawing logic"""
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = (dx*dx + dy*dy)**0.5  # Calculate distance
            
            if distance > 2.0:  # Use distance threshold instead of separate dx/dy
                self.x += dx * self.movement_speed
                self.y += dy * self.movement_speed
            else:
                # Snap to target and stop moving
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
        
        # Update rect position for collision detection
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    def draw(self, screen):
        """Draw the card - movement logic is now separate"""
        # Drawing logic only - movement is handled by update_movement()
        if self.is_face_up:
            if self.is_winner:
                pygame.draw.rect(screen, self.game.RED, self.rect)
                pygame.draw.rect(screen, self.game.BLACK, self.rect, 3)
                font = pygame.font.Font(None, 72)
                text = font.render("A", True, self.game.WHITE)
                text_rect = text.get_rect(center=self.rect.center)
                screen.blit(text, text_rect)
            else:
                pygame.draw.rect(screen, self.game.BLACK, self.rect)
                pygame.draw.rect(screen, self.game.WHITE, self.rect, 3)
                font = pygame.font.Font(None, 48)
                text = font.render("2", True, self.game.WHITE)
                text_rect = text.get_rect(center=self.rect.center)
                screen.blit(text, text_rect)
        else:
            pygame.draw.rect(screen, self.game.BLUE, self.rect)
            pygame.draw.rect(screen, self.game.BLACK, self.rect, 3)
            for i in range(3):
                for j in range(4):
                    pygame.draw.circle(screen, self.game.WHITE, 
                                     (self.rect.x + 30 + i * 30, 
                                      self.rect.y + 30 + j * 25), 8)
    
    def move_to(self, target_x, target_y):
        """Start moving to target position"""
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.moving = True