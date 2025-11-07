'''
Game Engine of the Snake Game.

functions:
- takes commands from the console
  - starts the game
  - returns the state of the game
  - prints the game state to the console
  - pauses and save the game to binary replay file
  - resume replay file
- validates apple placement from seeded random generator
- autosaves
'''

import random
from ReplayHandler import ReplayHandler
from Input import *

class GameEngine:
    APPLE = '@ '
    SNAKE = '# '
    HEAD = 'O '
    EMPTY = '. '

    REPLAY_FOLDER = 'replays/'
    UP = 'w'    # Move Up
    LEFT = 'a'  # Move Left
    DOWN = 's'  # Move Down
    RIGHT = 'd' # Move Right
    MOVEMENT_INPUTS = ''.join([UP, LEFT, DOWN, RIGHT])

    AUTOSAVE = 'autosave'
    AUTOSAVE_PATH = REPLAY_FOLDER + AUTOSAVE + '.bin'

    def __init__(self, width=10, height=10, input_source: Input=Player(), seed=None):
        self.width = width
        self.height = height
        self.input_source = input_source
        self.score = 0
        self.reason = 0  # 0: ongoing, 1: win, 2: collision
        self.segments = []
        self.current_segment = ''
        self.direction = self.RIGHT
        
        # Initialize random seed
        if seed is None:
            self.seed = random.randint(0, 2**32 - 1)
        else:
            self.seed = seed
        random.seed(self.seed)

        # Initialize game state
        self.snake = self.create_initial_snake()
        
        if type(self.input_source) == Replay:
            state = self.input_source.state
            self.width = state["width"]
            self.height = state["height"]
            self.seed = state["seed"]
            self.snake = state["snake"]

        self.spawn_apple()

        # Initialize the input Source
        input_source.updateState(self.get_game_state())

        # create autosave on init
        self.save_game(self.AUTOSAVE)

        print(self.get_game_state())
        pass

    def cord_to_index(self, x, y):
        '''
        Converts (x, y) coordinates to a single index.
        '''
        return y * self.width + x
    
    def index_to_cord(self, index):
        '''
        Converts a single index to (x, y) coordinates.
        '''
        x = index % self.width
        y = index // self.width
        return (x, y)

    def create_initial_snake(self):
        '''
        Spawns a three long snake in the middle.
        '''
        mid_x = self.width // 2
        mid_y = self.height // 2
        mid = self.cord_to_index(mid_x, mid_y)

        return [mid - 2, mid - 1, mid]

    def spawn_apple(self):
        '''
        Spawns an apple at a random location not occupied by the snake.
        
        Implementation with sets for efficiency.
        '''
        occupied = set(self.snake)
        all_positions = {pos for pos in range(self.width * self.width)}
        free_positions = list(all_positions - occupied)
        if not free_positions:
            self.apple = None  # No space left for an apple
            return
        self.apple = random.choice(free_positions)

        self.input_source.updateApple(self.apple)

    def print_game(self):
        '''
        Prints the current game state to the console with score.
        '''
        for y in range(self.height):
            row = ''
            for x in range(self.width):
                index = self.cord_to_index(x, y)
                if index == self.snake[-1]:
                    row += self.HEAD
                elif index in self.snake:
                    row += self.SNAKE
                elif index == self.apple:
                    row += self.APPLE
                else:
                    row += self.EMPTY
            print(row)
        print(f'\nScore: {self.score}\n')

    def get_game_state(self):
        '''
        Returns the current game state as a dictionary.
        '''
        return {
            'width': self.width,
            'height': self.height,
            'score': self.score,
            'apple': self.apple,
            'snake': self.snake
        }
    
    def save_game(self, filename: str):
        '''
        Saves the current game state to a binary replay file.
        '''

        if type(self.input_source) == Replay:
            return

        handler = ReplayHandler()

        dict_data = {
            "version": "5.0",
            "result": {"score": self.score, "reason": self.reason},
            "metadata": {
                "map": {"width": self.width, "height": self.height},
                "seed": self.seed,
                "initial": {"snake": self.create_initial_snake()}
            },
            "segments": self.segments
        }

        filepath = self.REPLAY_FOLDER + filename + '.bin'

        handler.encode_to_binary(dict_data, filepath)
    
    def loop(self):
        '''
        Main game loop.

        Takes in the commands from the console and processes them.
        '''
        print("Starting the game loop. Type 'exit' to quit.")
        while True:
            self.print_game()

            # Get Input from input_source
            command = self.input_source.getInput().lower()
            if command == 'quit':
                self.save_game(str(self.seed))
                print("Quit the game.")
                break
            elif command == 'state':
                state = self.get_game_state()
                print(state)
                next
            elif command == 'print':
                self.print_game()
                next
            # If command is only movement inputs, process them
            elif all(c in self.MOVEMENT_INPUTS for c in command):
                for move in command:
                    # Process each movement command
                    self.handle_input(move)

    def handle_input(self, move_char: str):
        '''
        Handles a single character input for movement.
        '''
        if move_char not in self.MOVEMENT_INPUTS:
            print("Invalid input. Use 'w', 'a', 's', 'd' for movement.")
            return
        # Movement processing logic would go here
        newHead = None
        if move_char == self.UP:
            newHead = self.snake[-1] - self.width
        elif move_char == self.LEFT:
            newHead = self.snake[-1] - 1
        elif move_char == self.DOWN:
            newHead = self.snake[-1] + self.width
        elif move_char == self.RIGHT:
            newHead = self.snake[-1] + 1
        
        self.snake.append(newHead)
        
        # Record movement in rotations as: 'L', 'R', 'S'
        if move_char == self.direction:
            self.current_segment += 'S'
        elif self.direction == self.UP and move_char == self.LEFT or \
             self.direction == self.LEFT and move_char == self.DOWN or \
             self.direction == self.DOWN and move_char == self.RIGHT or \
             self.direction == self.RIGHT and move_char == self.UP:
            self.current_segment += 'L'
        else:
            self.current_segment += 'R'

        # Update current direction
        self.direction = move_char

        # Collected apple check
        collected_apple = newHead == self.apple
        if collected_apple:
            self.spawn_apple()
            self.score += 1
            self.segments.append(self.current_segment)
            ReplayHandler().updateResult(self.AUTOSAVE_PATH, self.score, self.reason)
            ReplayHandler().addSegments(self.AUTOSAVE_PATH, [self.current_segment])
            self.current_segment = ''
        else:
            self.snake.pop(0)

        self.check_win()
        self.check_collisions()

    def check_collisions(self):
        '''
        Checks for collisions with walls or self.
        '''
        head = self.snake[-1]
        prev = self.snake[-2]
        x_head, y_head = self.index_to_cord(head)
        x_prev, y_prev = self.index_to_cord(prev)

        # Check wall collisions by measuring distance between head and previous segment
        if abs(x_head - x_prev) > 1 or abs(y_head - y_prev) > 1 or \
           head < 0 or head >= self.width * self.height:
            self.reason = 2  # collision
            print("Collision with wall! Game over.")
            self.save_game(str(self.seed))
            exit()

        # Check self collisions
        if head in self.snake[:-1]:
            self.reason = 2  # collision
            print("Collision with self! Game over.")
            self.save_game(str(self.seed))
            exit()

    def check_win(self):
        '''
        Checks if the player has won the game.
        '''
        if len(self.snake) == self.width * self.height:
            self.reason = 1  # win
            print("Congratulations! You've won the game!")
            self.save_game(str(self.seed))
            exit()

if __name__ == '__main__':
    # engine = GameEngine(width=6, height=6, input_source=Player(), seed=42)
    
    engine = GameEngine(width=10, height=10, input_source=Replay(), seed=42)
    engine.loop()