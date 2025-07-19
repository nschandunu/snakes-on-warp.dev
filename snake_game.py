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
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Snake
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Food
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Score
        
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
        """Draw the game border"""
        # Draw horizontal borders
        for x in range(self.box_x, self.box_x + self.box_width):
            self.stdscr.addch(self.box_y, x, curses.ACS_HLINE)
            self.stdscr.addch(self.box_y + self.box_height - 1, x, curses.ACS_HLINE)
        
        # Draw vertical borders
        for y in range(self.box_y, self.box_y + self.box_height):
            self.stdscr.addch(y, self.box_x, curses.ACS_VLINE)
            self.stdscr.addch(y, self.box_x + self.box_width - 1, curses.ACS_VLINE)
        
        # Draw corners
        self.stdscr.addch(self.box_y, self.box_x, curses.ACS_ULCORNER)
        self.stdscr.addch(self.box_y, self.box_x + self.box_width - 1, curses.ACS_URCORNER)
        self.stdscr.addch(self.box_y + self.box_height - 1, self.box_x, curses.ACS_LLCORNER)
        self.stdscr.addch(self.box_y + self.box_height - 1, self.box_x + self.box_width - 1, curses.ACS_LRCORNER)
    
    def draw_snake(self):
        """Draw the snake"""
        for i, segment in enumerate(self.snake):
            if i == 0:
                # Draw head with a different character
                self.stdscr.addch(segment[0], segment[1], '@', curses.color_pair(1) | curses.A_BOLD)
            else:
                # Draw body
                self.stdscr.addch(segment[0], segment[1], '#', curses.color_pair(1))
    
    def draw_food(self):
        """Draw the food"""
        self.stdscr.addch(self.food[0], self.food[1], '*', curses.color_pair(2) | curses.A_BOLD)
    
    def draw_score(self):
        """Draw the current score"""
        score_text = f"Score: {self.score}"
        self.stdscr.addstr(0, 2, score_text, curses.color_pair(3) | curses.A_BOLD)
        
        # Draw instructions
        instructions = "Use arrow keys to move, 'q' to quit"
        self.stdscr.addstr(self.height - 1, 2, instructions[:self.width - 4])
    
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
        """Display game over screen"""
        self.stdscr.clear()
        
        # Game over message
        game_over_text = "GAME OVER!"
        final_score_text = f"Final Score: {self.score}"
        restart_text = "Press any key to play again, or 'q' to quit"
        
        # Center the text
        y_center = self.height // 2
        x_center = self.width // 2
        
        self.stdscr.addstr(y_center - 2, x_center - len(game_over_text) // 2, 
                          game_over_text, curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(y_center, x_center - len(final_score_text) // 2, 
                          final_score_text, curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(y_center + 2, x_center - len(restart_text) // 2, restart_text)
        
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
