import json
import struct
import pygame
import time
from pathlib import Path

# -----------------------------
# Optional binary decoder (from earlier)
# -----------------------------
DIRECTION_MAP = {"w":0, "d":1, "s":2, "a":3}
REVERSE_DIR = {v:k for k,v in DIRECTION_MAP.items()}

class SnakeBinaryReplay:
    HEADER_MAGIC = b"SNAK"

    @staticmethod
    def decode_moves(data, count):
        moves = []
        bitstring = int.from_bytes(data, "big")
        total_bits = len(data) * 8
        for i in range(count):
            shift = total_bits - (i + 1) * 2
            val = (bitstring >> shift) & 0b11
            moves.append(REVERSE_DIR[val])
        return moves

    def load(self, path):
        with open(path, "rb") as f:
            data = f.read()
        offset = 0
        assert data[offset:offset+4] == self.HEADER_MAGIC
        offset += 4

        version, width, height, snake_len = struct.unpack_from("BHHB", data, offset)
        offset += struct.calcsize("BHHB")
        snake = [tuple(data[offset+i*2:offset+i*2+2]) for i in range(snake_len)]
        offset += snake_len * 2

        direction = REVERSE_DIR[data[offset]]
        offset += 1

        segment_count, = struct.unpack_from("H", data, offset)
        offset += 2

        segments = []
        for _ in range(segment_count):
            apple_x, apple_y, move_len = struct.unpack_from("BBH", data, offset)
            offset += 4
            move_bytes_len = (move_len * 2 + 7) // 8
            move_bytes = data[offset:offset+move_bytes_len]
            offset += move_bytes_len
            moves = self.decode_moves(move_bytes, move_len)
            length, = struct.unpack_from("H", data, offset)
            offset += 2
            segments.append({"apple": [apple_x, apple_y], "moves": moves, "length": length})

        return {
            "metadata": {"map": {"width": width, "height": height},
                         "initial": {"snake": snake, "direction": direction}},
            "segments": segments
        }


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
        self.direction = init["direction"]

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.map_w * self.CELL_SIZE, self.map_h * self.CELL_SIZE)
        )
        pygame.display.set_caption("Snake Replay Viewer")
        self.clock = pygame.time.Clock()

    def draw_cell(self, pos, color):
        x, y = pos
        rect = pygame.Rect(x * self.CELL_SIZE, y * self.CELL_SIZE,
                           self.CELL_SIZE, self.CELL_SIZE)
        pygame.draw.rect(self.screen, color, rect)
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
            (x * self.CELL_SIZE + self.CELL_SIZE // 2,
             y * self.CELL_SIZE + self.CELL_SIZE // 2)
            for x, y in self.snake
        ]

        # Draw body line
        pygame.draw.lines(self.screen, self.SNAKE_COLOR, False, points, self.CELL_SIZE // 3)

        # --- Draw head circle ---
        hx, hy = points[-1]
        pygame.draw.circle(self.screen, self.HEAD_COLOR, (hx, hy), self.CELL_SIZE // 3)

        # --- Draw eyes ---
        # Determine facing direction based on last two points
        if len(points) >= 2:
            x1, y1 = points[-2]
            x2, y2 = points[-1]
            dx = x2 - x1
            dy = y2 - y1

            # Normalize direction to one of four main axes
            if abs(dx) > abs(dy):
                dir_x = 1 if dx > 0 else -1
                dir_y = 0
            else:
                dir_x = 0
                dir_y = 1 if dy > 0 else -1

            # Eye placement offsets (slightly forward and sideways)
            head_radius = self.CELL_SIZE // 3
            eye_offset_forward = head_radius * 0.6
            eye_offset_side = head_radius * 0.4

            # Compute perpendicular vector
            perp_x, perp_y = -dir_y, dir_x

            # Base (center of head)
            base_x, base_y = hx, hy

            # Eye centers
            left_eye = (
                base_x + dir_x * eye_offset_forward + perp_x * eye_offset_side,
                base_y + dir_y * eye_offset_forward + perp_y * eye_offset_side
            )
            right_eye = (
                base_x + dir_x * eye_offset_forward - perp_x * eye_offset_side,
                base_y + dir_y * eye_offset_forward - perp_y * eye_offset_side
            )

            # Draw eyes
            eye_radius = max(2, self.CELL_SIZE // 8)
            pygame.draw.circle(self.screen, (255, 255, 255), left_eye, eye_radius)
            pygame.draw.circle(self.screen, (255, 255, 255), right_eye, eye_radius)


    def move_snake(self, direction, apple):
        head_x, head_y = self.snake[-1]
        if direction == "w": head_y -= 1
        elif direction == "s": head_y += 1
        elif direction == "a": head_x -= 1
        elif direction == "d": head_x += 1
        new_head = (head_x, head_y)
        self.snake.append(new_head)

        # Check for apple
        if self.snake[-1] != apple:
            self.snake.pop(0)

    def play(self):
        for segment in self.replay["segments"]:
            apple = tuple(segment["apple"])
            moves = segment["moves"]
            length_target = segment["length"]

            for move in moves:
                # Event handling for quitting
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

                # Move snake
                self.move_snake(move, apple)

                # Draw frame
                # Draw checkerboard background
                self.draw_checkerboard()

                # Draw apple as a circle
                ax, ay = apple
                pygame.draw.circle(
                    self.screen,
                    self.APPLE_COLOR,
                    (ax * self.CELL_SIZE + self.CELL_SIZE // 2,
                    ay * self.CELL_SIZE + self.CELL_SIZE // 2),
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
def load_replay(path):
    p = Path(path)
    if p.suffix == ".json":
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    elif p.suffix == ".bin":
        return SnakeBinaryReplay().load(p)
    else:
        raise ValueError("Unsupported replay format (use .json or .bin)")

if __name__ == "__main__":
    # path = input("Enter replay file (.json or .bin): ").strip()
    path = "snake_replay.json".strip()
    replay = load_replay(path)
    viewer = SnakeReplayViewer(replay)
    viewer.play()
