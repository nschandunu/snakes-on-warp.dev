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

class SnakeGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
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
        
        # Generate first food
        self.food = self.generate_food()
        
        # Score
        self.score = 0
        
        # Game speed (delay in seconds)
        self.delay = 0.1
        
    def generate_food(self):
        """Generate food at a random location not occupied by the snake"""
        while True:
            food_y = random.randint(self.box_y + 1, self.box_y + self.box_height - 2)
            food_x = random.randint(self.box_x + 1, self.box_x + self.box_width - 2)
            if [food_y, food_x] not in self.snake:
                return [food_y, food_x]
    
    def draw_border(self):
        """Draw the modern game border with Unicode box drawing characters"""
        # Modern Unicode box drawing characters
        horizontal = '═'
        vertical = '║'
        top_left = '╔'
        top_right = '╗'
        bottom_left = '╚'
        bottom_right = '╝'
        
        # Draw horizontal borders with style
        for x in range(self.box_x + 1, self.box_x + self.box_width - 1):
            self.stdscr.addstr(self.box_y, x, horizontal, curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(self.box_y + self.box_height - 1, x, horizontal, curses.color_pair(5) | curses.A_BOLD)
        
        # Draw vertical borders with style
        for y in range(self.box_y + 1, self.box_y + self.box_height - 1):
            self.stdscr.addstr(y, self.box_x, vertical, curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(y, self.box_x + self.box_width - 1, vertical, curses.color_pair(5) | curses.A_BOLD)
        
        # Draw corners with style
        self.stdscr.addstr(self.box_y, self.box_x, top_left, curses.color_pair(5) | curses.A_BOLD)
        self.stdscr.addstr(self.box_y, self.box_x + self.box_width - 1, top_right, curses.color_pair(5) | curses.A_BOLD)
        self.stdscr.addstr(self.box_y + self.box_height - 1, self.box_x, bottom_left, curses.color_pair(5) | curses.A_BOLD)
        self.stdscr.addstr(self.box_y + self.box_height - 1, self.box_x + self.box_width - 1, bottom_right, curses.color_pair(5) | curses.A_BOLD)
    
    def draw_snake(self):
        """Draw the snake with modern Unicode characters"""
        for i, segment in enumerate(self.snake):
            if i == 0:
                # Draw head with modern Unicode character based on direction
                if self.direction == [0, 1]:    # Moving right
                    head_char = '▶'
                elif self.direction == [0, -1]:  # Moving left
                    head_char = '◀'
                elif self.direction == [-1, 0]:  # Moving up
                    head_char = '▲'
                elif self.direction == [1, 0]:   # Moving down
                    head_char = '▼'
                else:
                    head_char = '●'  # Default head
                self.stdscr.addstr(segment[0], segment[1], head_char, curses.color_pair(2) | curses.A_BOLD)
            else:
                # Draw body with modern Unicode character
                self.stdscr.addstr(segment[0], segment[1], '●', curses.color_pair(1) | curses.A_BOLD)
    
    def draw_food(self):
        """Draw the food with modern styling"""
        # Use a more appealing food character
        food_char = '♥'  # Heart symbol for food
        self.stdscr.addstr(self.food[0], self.food[1], food_char, curses.color_pair(3) | curses.A_BOLD)
    
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
    
    def get_input(self):
        """Get user input and update direction"""
        self.stdscr.timeout(int(self.delay * 1000))  # Convert to milliseconds
        key = self.stdscr.getch()
        
        if key == ord('q'):
            return False
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
        
        if ate_food:
            self.score += 10
            self.food = self.generate_food()
            # Increase speed slightly
            if self.delay > 0.05:
                self.delay *= 0.95
        else:
            # Remove tail if no food eaten
            self.snake.pop()
        
        # Add new head
        self.snake.insert(0, new_head)
        
        return ate_food
    
    def check_collision(self):
        """Check for collisions with walls or self"""
        head = self.snake[0]
        
        # Check wall collision
        if (head[0] <= self.box_y or head[0] >= self.box_y + self.box_height - 1 or
            head[1] <= self.box_x or head[1] >= self.box_x + self.box_width - 1):
            return True
        
        # Check self collision
        if head in self.snake[1:]:
            return True
        
        return False
    
    def game_over_screen(self):
        """Display enhanced game over screen"""
        self.stdscr.clear()
        
        # Enhanced game over message with emojis
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
            self.draw_snake()
            self.draw_food()
            self.draw_score()
            
            # Refresh screen
            self.stdscr.refresh()
            
            # Get input
            if not self.get_input():
                break
            
            # Move snake
            self.move_snake()
            
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
