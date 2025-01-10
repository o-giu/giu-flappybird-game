# by Giu
# https://github.com/o-giu

import pygame
import random
import sys
import math
from enum import Enum, auto
from typing import List, Tuple
from dataclasses import dataclass
from pathlib import Path
from cryptography.fernet import Fernet

@dataclass
class GameConfig:
    WINDOW_SIZE: Tuple[int, int] = (800, 600)
    BIRD_SIZE: Tuple[int, int] = (40, 30)
    PIPE_WIDTH: int = 80
    GAP_SIZE: int = 200
    COLORS: dict = None

    def __post_init__(self):
        self.COLORS = {
            'background': (135, 206, 235),  # Sky blue
            'bird': (255, 255, 0),         # Yellow
            'pipe': (34, 139, 34),         # Forest green
            'text': (255, 255, 255),       # White
            'inactive_text': (128, 128, 128),  # Gray
            'ground': (139, 69, 19)        # Brown
        }

class Bird:
    def __init__(self, config: GameConfig):
        self.config = config
        self.wing_angle = 0
        self.wing_speed = 8
        self.eye_blink = 0
        self.colors = {
            'body': (255, 223, 0),     # Golden yellow
            'wing': (255, 150, 0),     # Orange
            'beak': (255, 69, 0),      # Red-orange
            'eye': (0, 0, 0),          # Black
            'eye_white': (255, 255, 255) # White
        }
        self.reset()
        
    def reset(self):
        self.x = self.config.WINDOW_SIZE[0] // 3
        self.y = self.config.WINDOW_SIZE[1] // 2
        self.velocity = 0
        self.gravity = 0.5
        self.flap_strength = -6
        self.rect = pygame.Rect(self.x, self.y, 
                              self.config.BIRD_SIZE[0], 
                              self.config.BIRD_SIZE[1])
        self.angle = 0

    def flap(self):
        self.velocity = self.flap_strength

    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity
        self.angle = max(-30, min(self.velocity * 3, 90))
        self.rect.y = self.y

    def draw(self, screen):
        # Create surface for rotation
        bird_surface = pygame.Surface(self.config.BIRD_SIZE, pygame.SRCALPHA)
        
        # Body
        pygame.draw.ellipse(bird_surface, self.colors['body'],
                          (5, 0, self.config.BIRD_SIZE[0]-10, self.config.BIRD_SIZE[1]))
        
        # Wing animation
        self.wing_angle = (self.wing_angle + self.wing_speed) % 360
        wing_offset = abs(math.sin(math.radians(self.wing_angle))) * 5
        wing_points = [
            (15, self.config.BIRD_SIZE[1]//2),
            (5, self.config.BIRD_SIZE[1]//2 + wing_offset),
            (15, self.config.BIRD_SIZE[1]//2 + wing_offset*2)
        ]
        pygame.draw.polygon(bird_surface, self.colors['wing'], wing_points)
        
        # Beak
        pygame.draw.polygon(bird_surface, self.colors['beak'], [
            (self.config.BIRD_SIZE[0]-10, self.config.BIRD_SIZE[1]//2-5),
            (self.config.BIRD_SIZE[0], self.config.BIRD_SIZE[1]//2),
            (self.config.BIRD_SIZE[0]-10, self.config.BIRD_SIZE[1]//2+5)
        ])
        
        # Eye animation (blinking)
        self.eye_blink = max(0, self.eye_blink - 1)
        if random.random() < 0.01:  # 1% chance to start blinking
            self.eye_blink = 5
            
        if self.eye_blink == 0:
            pygame.draw.circle(bird_surface, self.colors['eye_white'],
                             (self.config.BIRD_SIZE[0]-15, self.config.BIRD_SIZE[1]//2-5), 5)
            pygame.draw.circle(bird_surface, self.colors['eye'],
                             (self.config.BIRD_SIZE[0]-15, self.config.BIRD_SIZE[1]//2-5), 3)
        else:
            pygame.draw.line(bird_surface, self.colors['eye'],
                           (self.config.BIRD_SIZE[0]-18, self.config.BIRD_SIZE[1]//2-5),
                           (self.config.BIRD_SIZE[0]-12, self.config.BIRD_SIZE[1]//2-5), 2)
        
        # Rotate bird based on velocity
        rotated_surface = pygame.transform.rotate(bird_surface, -self.angle)
        screen.blit(rotated_surface, 
                   (self.x - (rotated_surface.get_width() - self.config.BIRD_SIZE[0]) // 2,
                    self.y - (rotated_surface.get_height() - self.config.BIRD_SIZE[1]) // 2))

class Pipe:
    def __init__(self, config: GameConfig, x: int):
        self.config = config
        self.x = x
        self.base_speed = 3
        self.speed = self.base_speed
        self.passed = False
        self.gap_y = random.randint(200, self.config.WINDOW_SIZE[1] - 200)
        self.top_rect = pygame.Rect(x, 0, config.PIPE_WIDTH, 
                                  self.gap_y - config.GAP_SIZE // 2)
        self.bottom_rect = pygame.Rect(x, self.gap_y + config.GAP_SIZE // 2,
                                     config.PIPE_WIDTH,
                                     config.WINDOW_SIZE[1] - (self.gap_y + config.GAP_SIZE // 2))
        self.shine_offset = random.randint(0, 360)

    def draw(self, screen):
        for rect in [self.top_rect, self.bottom_rect]:
            # Main pipe body
            pygame.draw.rect(screen, (34, 139, 34), rect)  # Dark green
            
            # Pipe edge
            edge_rect = rect.copy()
            edge_rect.width = 10
            pygame.draw.rect(screen, (20, 80, 20), edge_rect)  # Darker green
            
            # Pipe highlight
            highlight_rect = rect.copy()
            highlight_rect.x += 10
            highlight_rect.width = 5
            pygame.draw.rect(screen, (50, 205, 50), highlight_rect)  # Light green
            
            # Moving shine effect
            shine_y = (pygame.time.get_ticks() // 20 + self.shine_offset) % rect.height
            shine_rect = pygame.Rect(rect.x + 20, rect.y + shine_y, 3, 20)
            if shine_rect.bottom > rect.bottom:
                shine_rect.height = rect.bottom - shine_rect.top
            pygame.draw.rect(screen, (144, 238, 144), shine_rect)  # Light green shine

            # Pipe top/bottom caps
            cap_height = 20
            if rect == self.top_rect:
                cap_rect = pygame.Rect(rect.x - 5, rect.bottom - cap_height,
                                     rect.width + 10, cap_height)
            else:
                cap_rect = pygame.Rect(rect.x - 5, rect.top,
                                     rect.width + 10, cap_height)
            pygame.draw.rect(screen, (20, 80, 20), cap_rect)  # Darker green for caps

    def update(self):
        # Increase speed based on game progression (handled in FlappyBird class)
        self.x -= self.speed
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

class ScoreManager:
    def __init__(self):
        self.save_dir = Path('save')
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.save_dir / 'flappy_bird_score.key'
        self.score_file = self.save_dir / 'flappy_bird_score.encrypted'
        self._initialize_encryption()

    def _initialize_encryption(self):
        try:
            if self.key_file.exists():
                self.key = self.key_file.read_bytes()
            else:
                self.key = Fernet.generate_key()
                self.key_file.write_bytes(self.key)
            self.fernet = Fernet(self.key)
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            self.key = Fernet.generate_key()
            self.fernet = Fernet(self.key)

    def load_high_score(self) -> int:
        try:
            if self.score_file.exists():
                encrypted_data = self.score_file.read_bytes()
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return int(decrypted_data.decode())
        except Exception as e:
            print(f"Error loading high score: {e}")
        return 0

    def save_high_score(self, score: int):
        try:
            encrypted_data = self.fernet.encrypt(str(score).encode())
            self.score_file.write_bytes(encrypted_data)
        except Exception as e:
            print(f"Error saving high score: {e}")

class FlappyBird:
    def __init__(self):
        pygame.init()
        self.config = GameConfig()
        self.screen = pygame.display.set_mode(self.config.WINDOW_SIZE)
        pygame.display.set_caption("Giu - Flappy Bird v1.0")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        self.start_time = pygame.time.get_ticks()
        self.difficulty_factor = 1.0
        
        self.score_manager = ScoreManager()
        self.high_score = self.score_manager.load_high_score()
        self.reset_game()

    def reset_game(self):
        self.bird = Bird(self.config)
        self.pipes = []
        self.spawn_pipe()
        self.score = 0
        self.game_over = False
        self.start_time = pygame.time.get_ticks()
        self.difficulty_factor = 1.0

    def spawn_pipe(self):
        self.pipes.append(Pipe(self.config, self.config.WINDOW_SIZE[0]))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "pause"
                elif event.key == pygame.K_SPACE:
                    self.bird.flap()
        return "continue"

    def update(self):
        if self.game_over:
            return

        self.bird.update()

        # Update difficulty based on time
        elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000  # seconds
        self.difficulty_factor = min(3.0, 1.0 + elapsed_time / 30)
        
        # Apply difficulty to pipe speed and gap size
        for pipe in self.pipes:
            pipe.speed = pipe.base_speed * self.difficulty_factor
            pipe.config.GAP_SIZE = max(120, 200 - (self.difficulty_factor - 1) * 100)  # Shrink gap size

        # Spawn new pipes
        if not self.pipes or self.pipes[-1].x < self.config.WINDOW_SIZE[0] - 500:
            self.spawn_pipe()

        # Update pipes
        for pipe in self.pipes:
            pipe.update()
            
            # Score when passing pipes
            if not pipe.passed and pipe.x + self.config.PIPE_WIDTH < self.bird.x:
                pipe.passed = True
                self.score += 1

        # Remove off-screen pipes
        self.pipes = [pipe for pipe in self.pipes if pipe.x + self.config.PIPE_WIDTH > 0]

        # Check collisions
        if (self.bird.y < 0 or 
            self.bird.y + self.config.BIRD_SIZE[1] > self.config.WINDOW_SIZE[1]):
            self.game_over = True

        for pipe in self.pipes:
            if (pipe.top_rect.colliderect(self.bird.rect) or 
                pipe.bottom_rect.colliderect(self.bird.rect)):
                self.game_over = True

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        
        # Draw ground
        pygame.draw.rect(self.screen, self.config.COLORS['ground'],
                        (0, self.config.WINDOW_SIZE[1] - 20, 
                         self.config.WINDOW_SIZE[0], 20))

        for pipe in self.pipes:
            pipe.draw(self.screen)
            
        self.bird.draw(self.screen)

        # Draw score
        score_text = self.font.render(f'Score: {self.score}', True, 
                                    self.config.COLORS['text'])
        high_score_text = self.font.render(f'High Score: {self.high_score}', True, 
                                         self.config.COLORS['text'])
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(high_score_text, (self.config.WINDOW_SIZE[0] - 200, 10))

        pygame.display.flip()

    def run(self):
        try:
            while True:
                menu = Menu(self.screen, self.font, self.config)
                menu_running = True
                while menu_running:
                    menu.draw()
                    selection = menu.handle_input()
                    if selection == 0:  # Start Game
                        menu_running = False
                    elif selection == 1:  # Quit
                        return

                self.reset_game()
                game_running = True
                
                while game_running:
                    input_result = self.handle_input()
                    
                    if input_result == "quit":
                        return
                    elif input_result == "pause":
                        pause_menu = PauseMenu(self.screen, self.font, self.config)
                        paused = True
                        while paused:
                            pause_menu.draw()
                            pause_selection = pause_menu.handle_input()
                            if pause_selection == 0:  # Return to Game
                                paused = False
                            elif pause_selection == 1:  # Back to Menu
                                game_running = False
                                paused = False
                            elif pause_selection == 2:  # Quit
                                return

                    if not game_running:
                        break

                    if not self.game_over:
                        self.update()
                        self.draw()
                    else:
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.score_manager.save_high_score(self.high_score)
                            
                        game_over = GameOver(self.screen, self.font, 
                                           self.config, self.score)
                        game_over_running = True
                        while game_over_running:
                            game_over.draw()
                            game_over_selection = game_over.handle_input()
                            if game_over_selection == 0:  # Play Again
                                self.reset_game()
                                game_over_running = False
                            elif game_over_selection == 1:  # Main Menu
                                game_running = False
                                game_over_running = False
                            elif game_over_selection == 2:  # Quit
                                return

                    self.clock.tick(60)

        finally:
            pygame.quit()

class Menu:
    def __init__(self, screen, font, config):
        self.screen = screen
        self.font = font
        self.config = config
        self.options = ["Start Game", "Quit"]
        self.selected_index = 0
        self._initialize_title()
        
    def _initialize_title(self):
        title = "Giu - Flappy Bird v1.0"
        gradient_colors = [
            (255, 255, 0),  # Yellow
            (255, 165, 0),  # Orange
            (255, 69, 0)    # Red-Orange
        ]
        
        title_font = pygame.font.Font(None, 72)
        self.title_surfaces = []
        total_width = 0
        
        for i, letter in enumerate(title):
            color_idx = (i / (len(title) - 1)) * (len(gradient_colors) - 1)
            base_idx = int(color_idx)
            next_idx = min(base_idx + 1, len(gradient_colors) - 1)
            blend = color_idx - base_idx
            
            color = tuple(
                int(gradient_colors[base_idx][j] * (1 - blend) + 
                    gradient_colors[next_idx][j] * blend)
                for j in range(3)
            )
            
            letter_surface = title_font.render(letter, True, color)
            self.title_surfaces.append((letter_surface, total_width))
            total_width += letter_surface.get_width()
        
        self.title_total_width = total_width

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        
        title_start_x = (self.config.WINDOW_SIZE[0] - self.title_total_width) // 2
        title_y = 100
        for surface, offset in self.title_surfaces:
            self.screen.blit(surface, (title_start_x + offset, title_y))
        
        for i, option in enumerate(self.options):
            color = (self.config.COLORS['text'] if i == self.selected_index 
                    else self.config.COLORS['inactive_text'])
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(
                center=(self.config.WINDOW_SIZE[0] // 2, 250 + i * 50))
            self.screen.blit(option_text, option_rect)
        
        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 1
        return -1

class GameOver:
    def __init__(self, screen, font, config, final_score):
        self.screen = screen
        self.font = font
        self.config = config
        self.final_score = final_score
        self.options = ["Play Again", "Main Menu", "Quit"]
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 72)

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        
        game_over_text = self.title_font.render("Game Over", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(
            center=(self.config.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font.render(f"Final Score: {self.final_score}", True, 
                                    self.config.COLORS['text'])
        score_rect = score_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 180))
        self.screen.blit(score_text, score_rect)

        for i, option in enumerate(self.options):
            color = (self.config.COLORS['text'] if i == self.selected_index 
                    else self.config.COLORS['inactive_text'])
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(
                center=(self.config.WINDOW_SIZE[0] // 2, 280 + i * 50))
            self.screen.blit(option_text, option_rect)

        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 1
        return -1

class PauseMenu:
    def __init__(self, screen, font, config):
        self.screen = screen
        self.font = font
        self.config = config
        self.options = ["Return to Game", "Back to Menu", "Quit"]
        self.selected_index = 0

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        pause_text = self.font.render("Paused", True, self.config.COLORS['text'])
        pause_rect = pause_text.get_rect(
            center=(self.config.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(pause_text, pause_rect)

        for i, option in enumerate(self.options):
            color = (self.config.COLORS['text'] if i == self.selected_index 
                    else self.config.COLORS['inactive_text'])
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(
                center=(self.config.WINDOW_SIZE[0] // 2, 200 + i * 50))
            self.screen.blit(option_text, option_rect)

        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 0
        return -1

if __name__ == "__main__":
    try:
        game = FlappyBird()
        game.run()
    except Exception as e:
        import traceback
        error_msg = f"An error occurred:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "Error", 0)
        except:
            input("Press Enter to exit...")
    finally:
        pygame.quit()
