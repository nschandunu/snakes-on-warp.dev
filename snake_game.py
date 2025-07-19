#!/usr/bin/env python3
"""
CYBER SNAKE - Futuristic Terminal Game
A next-generation snake game with cyberpunk aesthetics, particle effects,
and advanced UI/UX features. Experience the future of terminal gaming!

Controls:
  ↑↓←→  Move snake
  SPACE  Pause/Resume
  T      Cycle themes
  M      Toggle music
  ESC/Q  Quit
  R      Restart
"""

import curses
import random
import time
import json
import os
import math
import threading
from datetime import datetime
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn

class Particle:
    """Individual particle for visual effects"""
    def __init__(self, x, y, char='*', color=3, velocity=[0, 0], lifetime=30):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.velocity = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.age = 0
    
    def update(self):
        """Update particle position and age"""
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.age += 1
        return self.age < self.lifetime
    
    def get_char(self):
        """Get character based on age for fading effect"""
        fade_ratio = 1 - (self.age / self.lifetime)
        if fade_ratio > 0.7:
            return '★'
        elif fade_ratio > 0.4:
            return '✦'
        elif fade_ratio > 0.2:
            return '·'
        else:
            return '`'

class ParticleSystem:
    """Manages particle effects"""
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, count=8):
        """Add explosion particles"""
        for i in range(count):
            angle = (2 * math.pi * i) / count
            velocity = [math.cos(angle) * 0.3, math.sin(angle) * 0.5]
            self.particles.append(Particle(x, y, '★', random.choice([3, 4, 6]), velocity, 25))
    
    def add_trail(self, x, y, direction):
        """Add trail particles behind snake head"""
        opposite_dir = [-direction[0] * 0.2, -direction[1] * 0.2]
        self.particles.append(Particle(x, y, '·', 2, opposite_dir, 10))
    
    def add_sparkle(self, x, y):
        """Add sparkle effect for power-ups"""
        chars = ['✦', '✧', '★', '☆']
        colors = [2, 3, 4, 6]
        for _ in range(3):
            offset_x = random.uniform(-0.5, 0.5)
            offset_y = random.uniform(-0.5, 0.5)
            self.particles.append(Particle(
                x + offset_x, y + offset_y, 
                random.choice(chars), 
                random.choice(colors), 
                [0, 0], 15
            ))
    
    def update(self, box_y, box_x, box_height, box_width):
        """Update all particles"""
        self.particles = [p for p in self.particles if p.update() and 
                         box_y < p.y < box_y + box_height and 
                         box_x < p.x < box_x + box_width]
    
    def draw(self, stdscr):
        """Draw all particles"""
        for particle in self.particles:
            try:
                y, x = int(particle.y), int(particle.x)
                char = particle.get_char()
                stdscr.addstr(y, x, char, curses.color_pair(particle.color))
            except:
                pass  # Skip particles that can't be drawn

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
        
        # Futuristic cyberpunk theme system
        self.themes = {
            'cyberpunk': {
                'name': '🔮 CYBERPUNK 2077',
                'snake_head': '◈', 'snake_body': '◇',
                'food': '⧫', 'border': '━┃┏┓┗┛',
                'colors': {'head': 6, 'body': 2, 'food': 4, 'border': 3},
                'effects': ['neon_glow', 'scanner_lines']
            },
            'matrix': {
                'name': '🟢 MATRIX CODE',
                'snake_head': '⬢', 'snake_body': '⬡',
                'food': '◉', 'border': '▓▓▓▓▓▓',
                'colors': {'head': 2, 'body': 1, 'food': 6, 'border': 2},
                'effects': ['digital_rain', 'glitch']
            },
            'tron': {
                'name': '💙 TRON LEGACY',
                'snake_head': '●', 'snake_body': '○',
                'food': '◆', 'border': '═║╔╗╚╝',
                'colors': {'head': 2, 'body': 6, 'food': 4, 'border': 2},
                'effects': ['grid_lines', 'pulse']
            },
            'hologram': {
                'name': '🌈 HOLOGRAM',
                'snake_head': '⬢', 'snake_body': '⬣',
                'food': '✧', 'border': '━┃┏┓┗┛',
                'colors': {'head': 6, 'body': 3, 'food': 5, 'border': 4},
                'effects': ['rainbow', 'flicker']
            },
            'vaporwave': {
                'name': '🌸 VAPORWAVE',
                'snake_head': '◉', 'snake_body': '◎',
                'food': '★', 'border': '─│╭╮╰╯',
                'colors': {'head': 5, 'body': 4, 'food': 6, 'border': 3},
                'effects': ['synthwave', 'gradient']
            }
        }
        
        self.current_theme = 'cyberpunk'
        self.theme_cycling = False
        
        # Particle system for visual effects
        self.particle_system = ParticleSystem()
        self.animation_frame = 0
        self.glitch_effect = False
        self.pulse_counter = 0
        
        # Advanced UI features
        self.game_state = 'playing'  # 'playing', 'paused', 'menu'
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        self.paused = False
        
        # Enhanced visual effects
        self.screen_shake = 0
        self.flash_effect = 0
        self.rainbow_offset = 0
        self.digital_rain = []
        self.scanner_line_y = 0
        
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
    
    def draw_visual_effects(self):
        """Draw advanced visual effects based on current theme"""
        theme = self.themes[self.current_theme]
        effects = theme.get('effects', [])
        
        # Update animation frame
        self.animation_frame = (self.animation_frame + 1) % 60
        self.pulse_counter = (self.pulse_counter + 1) % 30
        
        # Scanner lines effect (cyberpunk)
        if 'scanner_lines' in effects:
            self.scanner_line_y = (self.scanner_line_y + 0.5) % self.box_height
            y = int(self.box_y + self.scanner_line_y)
            for x in range(self.box_x + 1, self.box_x + self.box_width - 1):
                try:
                    # Only draw if position is empty
                    char = self.stdscr.inch(y, x) & 0xFF
                    if char == ord(' '):
                        self.stdscr.addstr(y, x, '─', curses.color_pair(6) | curses.A_DIM)
                except:
                    pass
        
        # Digital rain effect (matrix)
        if 'digital_rain' in effects:
            if len(self.digital_rain) < 10:
                for _ in range(3):
                    x = random.randint(self.box_x + 1, self.box_x + self.box_width - 2)
                    self.digital_rain.append({'x': x, 'y': self.box_y + 1, 'char': random.choice('01'), 'life': 20})
            
            # Update and draw rain
            for rain in self.digital_rain[:]:
                try:
                    self.stdscr.addstr(int(rain['y']), rain['x'], rain['char'], 
                                     curses.color_pair(2) | curses.A_DIM)
                    rain['y'] += 0.3
                    rain['life'] -= 1
                    if rain['life'] <= 0 or rain['y'] >= self.box_y + self.box_height - 1:
                        self.digital_rain.remove(rain)
                except:
                    self.digital_rain.remove(rain)
        
        # Grid lines effect (tron)
        if 'grid_lines' in effects and self.animation_frame % 15 == 0:
            for y in range(self.box_y + 3, self.box_y + self.box_height - 1, 4):
                for x in range(self.box_x + 1, self.box_x + self.box_width - 1, 2):
                    try:
                        char = self.stdscr.inch(y, x) & 0xFF
                        if char == ord(' '):
                            self.stdscr.addstr(y, x, '·', curses.color_pair(6) | curses.A_DIM)
                    except:
                        pass
        
        # Pulse effect around snake head
        if 'pulse' in effects:
            head = self.snake[0]
            pulse_radius = 1 if self.pulse_counter < 15 else 0
            if pulse_radius > 0:
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        try:
                            y, x = head[0] + dy, head[1] + dx
                            if (self.box_y < y < self.box_y + self.box_height - 1 and
                                self.box_x < x < self.box_x + self.box_width - 1):
                                char = self.stdscr.inch(y, x) & 0xFF
                                if char == ord(' '):
                                    self.stdscr.addstr(y, x, '·', curses.color_pair(2) | curses.A_DIM)
                        except:
                            pass
        
        # Rainbow effect (hologram)
        if 'rainbow' in effects:
            self.rainbow_offset = (self.rainbow_offset + 1) % 7
        
        # Glitch effect
        if 'glitch' in effects and random.random() < 0.02:
            self.glitch_effect = 5
        
        if self.glitch_effect > 0:
            self.glitch_effect -= 1
            # Randomly distort some characters
            for _ in range(3):
                y = random.randint(self.box_y + 1, self.box_y + self.box_height - 2)
                x = random.randint(self.box_x + 1, self.box_x + self.box_width - 2)
                try:
                    glitch_chars = ['▓', '▒', '░', '█']
                    self.stdscr.addstr(y, x, random.choice(glitch_chars), 
                                     curses.color_pair(random.randint(1, 6)))
                except:
                    pass
    
    def draw_score(self):
        """Draw the current score with enhanced cyberpunk styling"""
        theme = self.themes[self.current_theme]
        theme_name = theme['name']
        
        # Calculate FPS
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
        else:
            self.fps_counter += 1
        
        # Enhanced cyberpunk HUD
        score_text = f"◢◤ SCORE: {self.score:04d} ◥◣"
        length_text = f"◢◤ LENGTH: {len(self.snake):02d} ◥◣"
        level_text = f"◢◤ LEVEL: {self.level:02d} ◥◣"
        
        # Advanced stats
        speed_percentage = int((1 - (self.delay / self.base_delay)) * 100)
        speed_text = f"◢◤ SPEED: {speed_percentage:02d}% ◥◣"
        
        # Display theme name
        self.stdscr.addstr(0, 2, theme_name, curses.color_pair(6) | curses.A_BOLD)
        
        # Main stats line
        stats_y = 1
        self.stdscr.addstr(stats_y, 2, score_text, curses.color_pair(4) | curses.A_BOLD)
        
        if self.width > 40:
            self.stdscr.addstr(stats_y, 25, length_text, curses.color_pair(1) | curses.A_BOLD)
        
        if self.width > 60:
            self.stdscr.addstr(stats_y, 45, level_text, curses.color_pair(2) | curses.A_BOLD)
        
        if self.width > 80:
            self.stdscr.addstr(stats_y, 65, speed_text, curses.color_pair(3) | curses.A_BOLD)
        
        # Power-up status
        if self.active_power_up:
            power_text = f"⚡ {self.active_power_up.upper()}: {self.power_up_duration}"
            self.stdscr.addstr(0, self.width - len(power_text) - 2, power_text, 
                             curses.color_pair(5) | curses.A_BOLD)
        
        # Pause indicator
        if self.paused:
            pause_text = "⏸️  PAUSED  ⏸️"
            self.stdscr.addstr(self.height // 2, self.width // 2 - len(pause_text) // 2, 
                             pause_text, curses.color_pair(6) | curses.A_BOLD | curses.A_BLINK)
        
        # Enhanced cyberpunk instructions
        instructions = "◢ SPACE:Pause ◤ T:Theme ◢ M:Audio ◤ ESC/Q:Quit ◢ R:Restart ◤"
        max_len = self.width - 4
        if len(instructions) > max_len:
            instructions = "SPACE:Pause • T:Theme • Q:Quit"
        
        # Draw instructions with cyberpunk styling
        self.stdscr.addstr(self.height - 1, (self.width - len(instructions)) // 2, 
                          instructions[:max_len], curses.color_pair(7) | curses.A_DIM)
    
    def cycle_theme(self):
        """Cycle through available themes"""
        theme_names = list(self.themes.keys())
        current_index = theme_names.index(self.current_theme)
        next_index = (current_index + 1) % len(theme_names)
        self.current_theme = theme_names[next_index]
    
    def get_input(self):
        """Get user input with enhanced cyberpunk controls"""
        if self.paused:
            self.stdscr.timeout(-1)  # Blocking input when paused
        else:
            self.stdscr.timeout(int(self.delay * 1000))  # Convert to milliseconds
        
        key = self.stdscr.getch()
        
        # Quit commands
        if key == ord('q') or key == 27:  # 27 is ESC
            return False
        
        # Pause/Resume
        elif key == ord(' '):
            self.paused = not self.paused
            return True
        
        # Restart game
        elif key == ord('r') or key == ord('R'):
            self.__init__(self.stdscr)
            return True
        
        # Theme switching
        elif key == ord('t') or key == ord('T'):
            self.cycle_theme()
            # Add sparkle effect when changing themes
            head = self.snake[0]
            self.particle_system.add_sparkle(head[1], head[0])
        
        # Toggle sound
        elif key == ord('m') or key == ord('M'):
            enabled = self.sound_manager.toggle_sound()
            # Visual feedback for sound toggle (optional)
            
        # Movement controls (only when not paused)
        elif not self.paused:
            if key == curses.KEY_UP and self.direction != [1, 0]:
                self.direction = [-1, 0]
                # Add trail particle
                head = self.snake[0]
                self.particle_system.add_trail(head[1], head[0], self.direction)
            elif key == curses.KEY_DOWN and self.direction != [-1, 0]:
                self.direction = [1, 0]
                head = self.snake[0]
                self.particle_system.add_trail(head[1], head[0], self.direction)
            elif key == curses.KEY_LEFT and self.direction != [0, 1]:
                self.direction = [0, -1]
                head = self.snake[0]
                self.particle_system.add_trail(head[1], head[0], self.direction)
            elif key == curses.KEY_RIGHT and self.direction != [0, -1]:
                self.direction = [0, 1]
                head = self.snake[0]
                self.particle_system.add_trail(head[1], head[0], self.direction)
        
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
            
            # Skip movement and effects when paused
            if not self.paused:
                # Move snake and check for trap
                move_result = self.move_snake()
                if move_result == 'trap':
                    # Add explosion effect for trap
                    head = self.snake[0]
                    self.particle_system.add_explosion(head[1], head[0], 12)
                    # Play collision sound and show explosion
                    self.sound_manager.play_sound('collision')
                    self.stdscr.refresh()
                    time.sleep(0.5)  # Brief pause to show explosion
                    
                    if self.game_over_screen():
                        # Reset game
                        self.__init__(self.stdscr)
                    else:
                        break
                
                # Check for collisions
                if self.check_collision():
                    # Add explosion effect for collision
                    head = self.snake[0]
                    self.particle_system.add_explosion(head[1], head[0], 10)
                    # Play collision sound and show explosion
                    self.sound_manager.play_sound('collision')
                    self.stdscr.refresh()
                    time.sleep(0.5)  # Brief pause to show explosion
                    
                    if self.game_over_screen():
                        # Reset game
                        self.__init__(self.stdscr)
                    else:
                        break
                
                # Add sparkle effects when eating food
                if move_result is True:  # Food was eaten
                    self.particle_system.add_sparkle(self.food[1], self.food[0])
            
            # Update particle system
            self.particle_system.update(self.box_y, self.box_x, self.box_height, self.box_width)
            
            # Draw visual effects
            self.draw_visual_effects()
            
            # Draw particles
            self.particle_system.draw(self.stdscr)


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
