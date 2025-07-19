#!/usr/bin/env python3
"""
Terminal Snake Game
A classic snake game that runs in the terminal using Python's curses library.
Use arrow keys to control the snake. Eat food to grow and increase your score.
Press 'q' to quit the game.
"""

import curses
import random
import time
import json
import os
from rich.console import Console
from rich.theme import Theme

# Sound system imports
try:
    import pygame
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("pygame not found. Install with 'pip install pygame' for sound effects.")

class SoundManager:
    """Manages all sound effects for the game"""
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self.sound_initialized = False
        
        if SOUND_AVAILABLE:
            try:
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                self.sound_initialized = True
                self.create_sound_effects()
            except Exception as e:
                print(f"Sound initialization failed: {e}")
                self.sound_initialized = False
    
    def create_sound_effects(self):
        """Generate simple sound effects using pygame"""
        if not self.sound_initialized:
            return
            
        try:
            import numpy as np
            
            # Sample rate
            sample_rate = 22050
            
            # Create eat sound (short beep)
            duration = 0.1
            frequency = 800
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                wave = 4096 * np.sin(2 * np.pi * frequency * i / sample_rate)
                # Apply fade out envelope
                envelope = max(0, 1 - (i / frames))
                arr[i][0] = wave * envelope
                arr[i][1] = wave * envelope
            
            self.sounds['eat'] = pygame.sndarray.make_sound(arr.astype(np.int16))
            
            # Create power-up sound (ascending beep)
            duration = 0.15
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                progress = i / frames
                frequency = 600 + (400 * progress)  # Rising frequency
                wave = 3000 * np.sin(2 * np.pi * frequency * i / sample_rate)
                envelope = max(0, 1 - (i / frames) ** 0.5)
                arr[i][0] = wave * envelope
                arr[i][1] = wave * envelope
            
            self.sounds['powerup'] = pygame.sndarray.make_sound(arr.astype(np.int16))
            
            # Create collision sound (harsh buzz)
            duration = 0.2
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                # Mix multiple frequencies for harsh sound
                wave1 = 2000 * np.sin(2 * np.pi * 220 * i / sample_rate)
                wave2 = 2000 * np.sin(2 * np.pi * 150 * i / sample_rate) 
                wave3 = 1000 * np.sin(2 * np.pi * 100 * i / sample_rate)
                wave = wave1 + wave2 + wave3
                envelope = max(0, 1 - (i / frames))
                arr[i][0] = wave * envelope
                arr[i][1] = wave * envelope
            
            self.sounds['collision'] = pygame.sndarray.make_sound(arr.astype(np.int16))
            
            # Create level up sound (triumphant chord)
            duration = 0.3
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                # Major chord frequencies
                wave1 = 1500 * np.sin(2 * np.pi * 523 * i / sample_rate)  # C
                wave2 = 1500 * np.sin(2 * np.pi * 659 * i / sample_rate)  # E
                wave3 = 1500 * np.sin(2 * np.pi * 784 * i / sample_rate)  # G
                wave = (wave1 + wave2 + wave3) / 3
                envelope = max(0, 1 - (i / frames) ** 2)
                arr[i][0] = wave * envelope
                arr[i][1] = wave * envelope
            
            self.sounds['levelup'] = pygame.sndarray.make_sound(arr.astype(np.int16))
            
        except ImportError:
            # If numpy is not available, create simple tones
            self.create_simple_sounds()
        except Exception as e:
            print(f"Failed to create sound effects: {e}")
    
    def create_simple_sounds(self):
        """Create simple sounds without numpy"""
        import array
        import math
        
        sample_rate = 22050
        
        # Simple eat sound
        duration = 0.1
        frames = int(duration * sample_rate)
        arr = array.array('h', [0] * frames * 2)
        
        for i in range(frames):
            wave = int(4096 * math.sin(2 * math.pi * 800 * i / sample_rate))
            envelope = max(0, 1 - (i / frames))
            wave = int(wave * envelope)
            arr[i * 2] = wave
            arr[i * 2 + 1] = wave
        
        sound_buffer = bytes(arr)
        self.sounds['eat'] = pygame.mixer.Sound(buffer=sound_buffer)
        
        # Add other simple sounds...
        self.sounds['powerup'] = self.sounds['eat']  # Reuse for simplicity
        self.sounds['collision'] = self.sounds['eat']
        self.sounds['levelup'] = self.sounds['eat']
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.enabled or not self.sound_initialized or sound_name not in self.sounds:
            return
            
        try:
            self.sounds[sound_name].play()
        except Exception as e:
            print(f"Failed to play sound {sound_name}: {e}")
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.enabled = not self.enabled
        return self.enabled

class SnakeGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        self.high_scores_file = "high_scores.json"
        self.high_scores = self.load_high_scores()
        
        # Theme and skin system
        self.themes = {
            'classic': {
                'name': 'Classic',
                'snake_head': '●', 'snake_body': '●',
                'food': '♥', 'border': '═║╔╗╚╝',
                'colors': {'head': 2, 'body': 1, 'food': 3, 'border': 5}
            },
            'retro': {
                'name': 'Retro', 
                'snake_head': '▓', 'snake_body': '▒',
                'food': '◆', 'border': '▬│┌┐└┘',
                'colors': {'head': 4, 'body': 2, 'food': 6, 'border': 1}
            },
            'modern': {
                'name': 'Modern',
                'snake_head': '◉', 'snake_body': '○',
                'food': '✦', 'border': '━┃┏┓┗┛',
                'colors': {'head': 6, 'body': 5, 'food': 4, 'border': 2}
            },
            'minimal': {
                'name': 'Minimal',
                'snake_head': '■', 'snake_body': '□',
                'food': '●', 'border': '─│╭╮╰╯',
                'colors': {'head': 7, 'body': 7, 'food': 1, 'border': 7}
            },
            'neon': {
                'name': 'Neon',
                'snake_head': '⬢', 'snake_body': '⬡',
                'food': '⭐', 'border': '═║╔╗╚╝',
                'colors': {'head': 6, 'body': 2, 'food': 4, 'border': 3}
            }
        }
        
        self.current_theme = 'classic'
        self.theme_cycling = False
        
        # Initialize sound system
        self.sound_manager = SoundManager()
        
        # Initialize rich console with custom theme
        self.console = Console()
        self.theme = Theme({
            "border": "blue",
            "snake_head": "cyan bold",
            "snake_body": "green bold",
            "food": "red bold",
            "score": "yellow bold",
            "text": "white"
        })

        self.console.push_theme(self.theme)

        # Initialize colors
        curses.curs_set(0)  # Hide cursor
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Snake body
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Snake head
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Food
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Score
        curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Border
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Game over
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)  # UI elements
        
        # Game settings
        self.box_height = self.height - 4
        self.box_width = self.width - 4
        self.box_y = 2
        self.box_x = 2
        
        # Initialize snake
        self.snake = [
            [self.box_y + self.box_height // 2, self.box_x + self.box_width // 2],
            [self.box_y + self.box_height // 2, self.box_x + self.box_width // 2 - 1],
            [self.box_y + self.box_height // 2, self.box_x + self.box_width // 2 - 2]
        ]
        
        # Initial direction (moving right)
        self.direction = [0, 1]
        
        # Score and level system
        self.score = 0
        self.level = 1
        self.score_for_next_level = 100  # Points needed for next level
        
        # Game speed (delay in seconds)
        self.delay = 0.15
        self.base_delay = 0.15
        
        # Power-ups system
        self.power_ups = []
        self.power_up_timer = 0
        self.power_up_spawn_chance = 0.05  # 5% chance per food eaten
        self.active_power_up = None
        self.power_up_duration = 0
        
        # Obstacles for higher levels
        self.obstacles = []
        
        # Initialize obstacles for level 1 (none)
        self.generate_obstacles()
        
        # Generate first food (after obstacles are initialized)
        self.food = self.generate_food()
        
    def generate_food(self):
        """Generate food at a random location not occupied by the snake"""
        while True:
            food_y = random.randint(self.box_y + 1, self.box_y + self.box_height - 2)
            food_x = random.randint(self.box_x + 1, self.box_x + self.box_width - 2)
            if [food_y, food_x] not in self.snake and [food_y, food_x] not in self.obstacles:
                return [food_y, food_x]
    
    def generate_power_up(self):
        """Generate a power-up at a random location"""
        power_up_types = [
            {'type': 'slow', 'char': '🍏', 'color': 1, 'duration': 100},  # Slow-mo fruit
            {'type': 'boost', 'char': '🚀', 'color': 2, 'duration': 50},   # Speed boost
            {'type': 'trap', 'char': '💣', 'color': 6, 'duration': 0}      # Trap
        ]
        
        while True:
            y = random.randint(self.box_y + 1, self.box_y + self.box_height - 2)
            x = random.randint(self.box_x + 1, self.box_x + self.box_width - 2)
            if ([y, x] not in self.snake and [y, x] != self.food and 
                [y, x] not in self.obstacles and 
                not any(pu['pos'] == [y, x] for pu in self.power_ups)):
                
                power_up = random.choice(power_up_types).copy()
                power_up['pos'] = [y, x]
                power_up['timer'] = 200  # Power-up disappears after 200 game ticks
                return power_up
    
    def generate_obstacles(self):
        """Generate obstacles based on current level"""
        self.obstacles = []
        obstacle_count = min(self.level - 1, 5)  # More obstacles at higher levels
        
        for _ in range(obstacle_count):
            while True:
                y = random.randint(self.box_y + 2, self.box_y + self.box_height - 3)
                x = random.randint(self.box_x + 2, self.box_x + self.box_width - 3)
                if ([y, x] not in self.snake and [y, x] != self.food and 
                    [y, x] not in self.obstacles):
                    self.obstacles.append([y, x])
                    break
    
    def draw_border(self):
        """Draw themed game border"""
        theme = self.themes[self.current_theme]
        border_chars = theme['border']
        
        # Extract border characters
        horizontal = border_chars[0]
        vertical = border_chars[1]
        top_left = border_chars[2]
        top_right = border_chars[3]
        bottom_left = border_chars[4]
        bottom_right = border_chars[5]
        
        border_color = theme['colors']['border']
        
        # Draw horizontal borders with theme style
        for x in range(self.box_x + 1, self.box_x + self.box_width - 1):
            self.stdscr.addstr(self.box_y, x, horizontal, curses.color_pair(border_color) | curses.A_BOLD)
            self.stdscr.addstr(self.box_y + self.box_height - 1, x, horizontal, curses.color_pair(border_color) | curses.A_BOLD)
        
        # Draw vertical borders with theme style
        for y in range(self.box_y + 1, self.box_y + self.box_height - 1):
            self.stdscr.addstr(y, self.box_x, vertical, curses.color_pair(border_color) | curses.A_BOLD)
            self.stdscr.addstr(y, self.box_x + self.box_width - 1, vertical, curses.color_pair(border_color) | curses.A_BOLD)
        
        # Draw corners with theme style
        self.stdscr.addstr(self.box_y, self.box_x, top_left, curses.color_pair(border_color) | curses.A_BOLD)
        self.stdscr.addstr(self.box_y, self.box_x + self.box_width - 1, top_right, curses.color_pair(border_color) | curses.A_BOLD)
        self.stdscr.addstr(self.box_y + self.box_height - 1, self.box_x, bottom_left, curses.color_pair(border_color) | curses.A_BOLD)
        self.stdscr.addstr(self.box_y + self.box_height - 1, self.box_x + self.box_width - 1, bottom_right, curses.color_pair(border_color) | curses.A_BOLD)
    
    def draw_snake(self):
        """Draw themed snake"""
        theme = self.themes[self.current_theme]
        
        for i, segment in enumerate(self.snake):
            if i == 0:
                # Draw head with directional character or theme head
                if self.direction == [0, 1]:    # Moving right
                    head_char = '▶'
                elif self.direction == [0, -1]:  # Moving left
                    head_char = '◀'
                elif self.direction == [-1, 0]:  # Moving up
                    head_char = '▲'
                elif self.direction == [1, 0]:   # Moving down
                    head_char = '▼'
                else:
                    head_char = theme['snake_head']  # Theme head as fallback
                
                head_color = theme['colors']['head']
                self.stdscr.addstr(segment[0], segment[1], head_char, curses.color_pair(head_color) | curses.A_BOLD)
            else:
                # Draw body with theme character
                body_char = theme['snake_body']
                body_color = theme['colors']['body']
                self.stdscr.addstr(segment[0], segment[1], body_char, curses.color_pair(body_color) | curses.A_BOLD)
    
    def draw_food(self):
        """Draw themed food"""
        theme = self.themes[self.current_theme]
        food_char = theme['food']
        food_color = theme['colors']['food']
        self.stdscr.addstr(self.food[0], self.food[1], food_char, curses.color_pair(food_color) | curses.A_BOLD)
    
    def draw_power_ups(self):
        """Draw all active power-ups"""
        for power_up in self.power_ups:
            try:
                # Use fallback characters if emojis don't work
                if power_up['type'] == 'slow':
                    char = 'S'  # Fallback for slow
                elif power_up['type'] == 'boost':
                    char = 'B'  # Fallback for boost  
                elif power_up['type'] == 'trap':
                    char = 'X'  # Fallback for trap
                else:
                    char = '?'
                    
                self.stdscr.addstr(power_up['pos'][0], power_up['pos'][1], char, 
                                 curses.color_pair(power_up['color']) | curses.A_BOLD)
            except:
                # If drawing fails, skip this power-up
                pass
    
    def draw_obstacles(self):
        """Draw all obstacles"""
        for obstacle in self.obstacles:
            self.stdscr.addstr(obstacle[0], obstacle[1], '█', curses.color_pair(6) | curses.A_BOLD)
    
    def draw_score(self):
        """Draw the current score with enhanced styling"""
        # Enhanced score display with emojis and styling
        score_text = f"🏆 Score: {self.score}"
        length_text = f"🐍 Length: {len(self.snake)}"
        speed_indicator = "⚡" * max(1, 5 - int(self.delay * 50))  # Speed indicator
        speed_text = f"Speed: {speed_indicator}"
        
        # Display score and stats
        self.stdscr.addstr(0, 2, score_text, curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.addstr(0, 20, length_text, curses.color_pair(1) | curses.A_BOLD)
        
        # Only show speed if there's enough room
        if self.width > 50:
            self.stdscr.addstr(0, 40, speed_text, curses.color_pair(2) | curses.A_BOLD)
        
        # Enhanced instructions with emojis
        instructions = "🎮 Use ↑↓←→ arrows to move • Press 'q' to quit"
        max_len = self.width - 4
        if len(instructions) > max_len:
            instructions = "Use arrow keys to move • 'q' to quit"
        self.stdscr.addstr(self.height - 1, 2, instructions[:max_len], curses.color_pair(7))
    
    def cycle_theme(self):
        """Cycle through available themes"""
        theme_names = list(self.themes.keys())
        current_index = theme_names.index(self.current_theme)
        next_index = (current_index + 1) % len(theme_names)
        self.current_theme = theme_names[next_index]
    
    def get_input(self):
        """Get user input and update direction"""
        self.stdscr.timeout(int(self.delay * 1000))  # Convert to milliseconds
        key = self.stdscr.getch()
        
        if key == ord('q'):
            return False
        elif key == ord('t'):  # Theme switching
            self.cycle_theme()
        elif key == curses.KEY_UP and self.direction != [1, 0]:
            self.direction = [-1, 0]
        elif key == curses.KEY_DOWN and self.direction != [-1, 0]:
            self.direction = [1, 0]
        elif key == curses.KEY_LEFT and self.direction != [0, 1]:
            self.direction = [0, -1]
        elif key == curses.KEY_RIGHT and self.direction != [0, -1]:
            self.direction = [0, 1]
        
        return True
    
    def move_snake(self):
        """Move the snake in the current direction"""
        head = self.snake[0]
        new_head = [head[0] + self.direction[0], head[1] + self.direction[1]]
        
        # Check if snake eats food
        ate_food = new_head == self.food
        ate_power_up = None
        
        # Check power-up collision
        for i, power_up in enumerate(self.power_ups[:]):
            if new_head == power_up['pos']:
                ate_power_up = power_up
                self.power_ups.pop(i)
                break
        
        if ate_food:
            self.sound_manager.play_sound('eat')  # Play eating sound
            self.score += 10
            self.food = self.generate_food()
            
            # Level progression
            if self.score >= self.score_for_next_level:
                self.sound_manager.play_sound('levelup')  # Play level up sound
                self.level += 1
                self.score_for_next_level += 50  # Increase requirement for next level
                self.generate_obstacles()  # Add obstacles for new level
            
            # Spawn power-up chance
            if random.random() < self.power_up_spawn_chance:
                new_power_up = self.generate_power_up()
                if new_power_up:
                    self.power_ups.append(new_power_up)
            
            # Increase speed slightly
            if self.delay > 0.05:
                self.delay *= 0.98
        else:
            # Remove tail if no food eaten
            self.snake.pop()
        
        # Handle power-up effects
        if ate_power_up:
            if ate_power_up['type'] == 'slow':
                self.sound_manager.play_sound('powerup')  # Play power-up sound
                self.delay = self.base_delay * 1.5  # Slow down
                self.active_power_up = 'slow'
                self.power_up_duration = ate_power_up['duration']
                self.score += 5
            elif ate_power_up['type'] == 'boost':
                self.sound_manager.play_sound('powerup')  # Play power-up sound
                self.delay = self.base_delay * 0.5  # Speed up
                self.active_power_up = 'boost'
                self.power_up_duration = ate_power_up['duration']
                self.score += 15
            elif ate_power_up['type'] == 'trap':
                self.sound_manager.play_sound('collision')  # Play trap sound
                return 'trap'  # Signal trap eaten
        
        # Update power-up duration
        if self.power_up_duration > 0:
            self.power_up_duration -= 1
            if self.power_up_duration == 0:
                self.active_power_up = None
                self.delay = self.base_delay  # Reset speed
        
        # Update power-up timers
        for power_up in self.power_ups[:]:
            power_up['timer'] -= 1
            if power_up['timer'] <= 0:
                self.power_ups.remove(power_up)
        
        # Add new head
        self.snake.insert(0, new_head)
        
        return ate_food
    
    def check_collision(self):
        """Check for collisions with walls, self, or obstacles"""
        head = self.snake[0]
        
        # Check wall collision
        if (head[0] <= self.box_y or head[0] >= self.box_y + self.box_height - 1 or
            head[1] <= self.box_x or head[1] >= self.box_x + self.box_width - 1):
            return True
        
        # Check self collision
        if head in self.snake[1:]:
            return True
        
        # Check obstacle collision
        if head in self.obstacles:
            return True
        
        return False
    
    def load_high_scores(self):
        """Load high scores from a JSON file"""
        if os.path.exists(self.high_scores_file):
            with open(self.high_scores_file, 'r') as file:
                return json.load(file)
        return []

    def save_high_score(self, score):
        """Save a high score to the JSON file"""
        self.high_scores.append(score)
        self.high_scores.sort(reverse=True)
        self.high_scores = self.high_scores[:5]  # Keep top 5 scores
        with open(self.high_scores_file, 'w') as file:
            json.dump(self.high_scores, file)

    def game_over_screen(self):
        """Display enhanced game over screen"""
        self.save_high_score(self.score)

        self.stdscr.clear()
        
        # Enhanced game over message with emojis
        high_score_text = "🏅 High Scores: " + ', '.join(map(str, self.high_scores))
        game_over_text = "💀 GAME OVER! 💀"
        final_score_text = f"🏆 Final Score: {self.score}"
        snake_length_text = f"🐍 Snake Length: {len(self.snake)}"
        restart_text = "⚡ Press any key to play again • 'q' to quit"
        
        # Center the text
        y_center = self.height // 2
        x_center = self.width // 2
        
        # Game over message with styling
        self.stdscr.addstr(y_center - 3, x_center - len(game_over_text) // 2, 
                          game_over_text, curses.color_pair(6) | curses.A_BOLD)
        
        # High scores information
        self.stdscr.addstr(y_center - 5, x_center - len(high_score_text) // 2, 
                          high_score_text, curses.color_pair(4) | curses.A_BOLD)

        # Score information
        self.stdscr.addstr(y_center - 1, x_center - len(final_score_text) // 2, 
                          final_score_text, curses.color_pair(4) | curses.A_BOLD)
        
        self.stdscr.addstr(y_center, x_center - len(snake_length_text) // 2, 
                          snake_length_text, curses.color_pair(1) | curses.A_BOLD)
        
        # Instructions
        self.stdscr.addstr(y_center + 2, x_center - len(restart_text) // 2, 
                          restart_text, curses.color_pair(7))
        
        # Add a decorative border around the game over message
        border_chars = "═" * (len(game_over_text) + 4)
        self.stdscr.addstr(y_center - 4, x_center - len(border_chars) // 2, 
                          border_chars, curses.color_pair(5) | curses.A_BOLD)
        self.stdscr.addstr(y_center + 3, x_center - len(border_chars) // 2, 
                          border_chars, curses.color_pair(5) | curses.A_BOLD)
        
        self.stdscr.refresh()
        
        # Wait for input
        self.stdscr.timeout(-1)  # Blocking input
        key = self.stdscr.getch()
        return key != ord('q')
    
    def run(self):
        """Main game loop"""
        while True:
            # Clear screen
            self.stdscr.clear()
            
            # Draw game elements
            self.draw_border()
            self.draw_obstacles()
            self.draw_snake()
            self.draw_food()
            self.draw_power_ups()
            self.draw_score()
            
            # Refresh screen
            self.stdscr.refresh()
            
            # Get input
            if not self.get_input():
                break
            
            # Move snake and check for trap
            move_result = self.move_snake()
            if move_result == 'trap':
                # Trap eaten - game over
                if self.game_over_screen():
                    # Reset game
                    self.__init__(self.stdscr)
                else:
                    break
            
            # Check for collisions
            if self.check_collision():
                if self.game_over_screen():
                    # Reset game
                    self.__init__(self.stdscr)
                else:
                    break


def main(stdscr):
    """Initialize and run the game"""
    # Check if terminal is large enough
    height, width = stdscr.getmaxyx()
    if height < 10 or width < 20:
        stdscr.addstr(0, 0, "Terminal too small! Please resize and try again.")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Enable keypad to capture arrow keys
    stdscr.keypad(True)
    
    # Create and run game
    game = SnakeGame(stdscr)
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nGame interrupted. Thanks for playing!")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure your terminal supports colors and is large enough to play.")
