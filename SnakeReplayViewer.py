import json
import struct
import pygame
import time
from pathlib import Path
from ReplayHandler import ReplayHandler

# -----------------------------
# Optional binary decoder (from earlier)
# -----------------------------
DIRECTION_MAP = {"w":0, "d":1, "s":2, "a":3}
REVERSE_DIR = {v:k for k,v in DIRECTION_MAP.items()}

# -----------------------------
# Snake Replay Viewer
# -----------------------------
class SnakeReplayViewer:
    CELL_SIZE = 50
    BG_LIGHT = (45, 45, 45)
    BG_DARK = (30, 30, 30)
    SNAKE_COLOR = (0, 255, 0)
    HEAD_COLOR = (50, 255, 50)
    APPLE_COLOR = (255, 60, 60)
    GRID_COLOR = (50, 50, 50)
    SPEED = 20  # frames per second


    def __init__(self, replay):
        self.replay = replay
        self.map_w = replay["metadata"]["map"]["width"]
        self.map_h = replay["metadata"]["map"]["height"]

        init = replay["metadata"]["initial"]
        self.snake = list(init["snake"])

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.map_w * self.CELL_SIZE, self.map_h * self.CELL_SIZE)
        )
        pygame.display.set_caption("Snake Replay Viewer")
        self.clock = pygame.time.Clock()

    def draw_checkerboard(self):
        for y in range(self.map_h):
            for x in range(self.map_w):
                color = self.BG_LIGHT if (x + y) % 2 == 0 else self.BG_DARK
                rect = pygame.Rect(
                    x * self.CELL_SIZE,
                    y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE
                )
                pygame.draw.rect(self.screen, color, rect)

    def draw_snake(self):
        if len(self.snake) < 2:
            return

        # Convert snake segment grid coordinates → pixel coordinates
        points = [
            (body % self.map_w * self.CELL_SIZE + self.CELL_SIZE // 2,
             body // self.map_w * self.CELL_SIZE + self.CELL_SIZE // 2)
            for body in self.snake
        ]

        # Draw body line
        pygame.draw.lines(self.screen, self.SNAKE_COLOR, False, points, self.CELL_SIZE // 3)

        # --- Draw head circle ---
        hx, hy = points[-1]
        pygame.draw.circle(self.screen, self.HEAD_COLOR, (hx, hy), self.CELL_SIZE // 3)


    def move_snake(self, direction, apple):
        new_head = self.snake[-1]
        if direction == 'w': new_head -= self.map_w
        elif direction == 's': new_head += self.map_w
        elif direction == 'a': new_head -= 1
        elif direction == 'd': new_head += 1
        self.snake.append(new_head)

        # Check for apple
        if self.snake[-1] != apple:
            self.snake.pop(0)

    def play(self):
        dir = 'd'  # Initial direction placeholder
        for segment in self.replay["segments"]:
            # Recalculate rotations into absolute directions
            moves = []
            for move in segment:
                if move == 'S':
                    moves.append(dir)
                elif move == 'L':
                    if dir == 'w': dir = 'a'
                    elif dir == 'a': dir = 's'
                    elif dir == 's': dir = 'd'
                    elif dir == 'd': dir = 'w'
                    moves.append(dir)
                elif move == 'R':
                    if dir == 'w': dir = 'd'
                    elif dir == 'd': dir = 's'
                    elif dir == 's': dir = 'a'
                    elif dir == 'a': dir = 'w'
                    moves.append(dir)

            # Get current apple position
            apple = self.snake[-1]
            for move in moves:
                if move == 'w': apple -= self.map_w
                elif move == 's': apple += self.map_w
                elif move == 'a': apple -= 1
                elif move == 'd': apple += 1

            for move in moves:
                # Event handling for quitting
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

                # Move snake
                self.move_snake(move, apple)

                # Draw checkerboard background
                self.draw_checkerboard()

                # Draw apple as a circle
                pygame.draw.circle(
                    self.screen,
                    self.APPLE_COLOR,
                    (apple % self.map_w * self.CELL_SIZE + self.CELL_SIZE // 2,
                    apple // self.map_w * self.CELL_SIZE + self.CELL_SIZE // 2),
                    self.CELL_SIZE // 3
                )

                # Draw snake line + eyes
                self.draw_snake()

                pygame.display.flip()
                self.clock.tick(self.SPEED)

        print("Replay finished.")
        time.sleep(1)
        pygame.quit()


# -----------------------------
# Main Entry
# -----------------------------

if __name__ == "__main__":
    path = input("Enter replay file (.bin): ").strip()

    replay = ReplayHandler().decode_to_dict(path)
    viewer = SnakeReplayViewer(replay)
    viewer.play()
