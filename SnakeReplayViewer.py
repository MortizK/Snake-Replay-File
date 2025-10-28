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
    CELL_SIZE = 25
    BG_COLOR = (30, 30, 30)
    SNAKE_COLOR = (0, 255, 0)
    APPLE_COLOR = (255, 60, 60)
    SPEED = 10  # frames per second

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
                self.screen.fill(self.BG_COLOR)
                self.draw_cell(apple, self.APPLE_COLOR)
                for segment_pos in self.snake:
                    self.draw_cell(segment_pos, self.SNAKE_COLOR)

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
