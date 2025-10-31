from random import seed, choice, randint
from ReplayHandler import ReplayHandler

# --- Game Config ---
WIDTH = 4
HEIGHT = 4
UP = "w"
LEFT = "a"
DOWN = "s"
RIGHT = "d"

# Initial state
start = HEIGHT // 2 * WIDTH
snake = [start, start + 1, start + 2]
apple = start + WIDTH - 1
game_seed = randint(0, 2**32 - 1)
seed(game_seed)

# Replay tracking
segments = []
current_segment = []

# --- Helper Functions ---
def cordToID(x, y) -> int:
    return y * WIDTH + x

def idToCord(id) -> list[int]:
    y = id // WIDTH
    x = id % WIDTH
    return [x, y]

def printBoard(snake, apple):
    string = ""
    for i in range(WIDTH * HEIGHT):
        if i % WIDTH == 0:
            string += "\n"
        if i in snake:
            string += "# "
        elif i == apple:
            string += "@ "
        else:
            string += ". "
    print(string)

def newApple(snake, newHead):
    all_cells = set(range(WIDTH * HEIGHT))
    free_cells = list(all_cells - set(snake) - {newHead})
    if not free_cells:
        return None  # No free space left, game should end
    return choice(free_cells)

def dirToChar(last_dir, dir):
    if dir == last_dir:
        return 'S'
    elif (last_dir == UP and dir == LEFT) or (last_dir == LEFT and dir == DOWN) or (last_dir == DOWN and dir == RIGHT) or (last_dir == RIGHT and dir == UP):
        return 'L'
    else:
        return 'R'

# --- Game Loop ---
printBoard(snake, apple)
score = 0
reason = None
last_dir = RIGHT

while True:
    dir = input("Move (w/a/s/d, q to quit): ").lower()

    if dir == "q":
        reason = 3
        break

    while dir not in [UP, DOWN, LEFT, RIGHT]:
        dir = input("Invalid! Use w/a/s/d: ").lower()

    newHead = None
    if dir == UP:
        newHead = snake[-1] - WIDTH
    elif dir == LEFT:
        newHead = snake[-1] - 1
    elif dir == DOWN:
        newHead = snake[-1] + WIDTH
    elif dir == RIGHT:
        newHead = snake[-1] + 1

    # Update snake And Track Replay
    collected_apple = newHead == apple
    current_segment.append(dirToChar(last_dir, dir))
    if collected_apple:
        apple = newApple(snake, newHead)
        score += 1
        segments.append(''.join(current_segment))
        current_segment = []
    else:
        tail = snake.pop(0)
    last_dir = dir

    # Game over checks
    if len(snake) == HEIGHT * WIDTH - 1:
        print("YOU WIN")
        reason = 1
        break
    elif newHead in snake or newHead < 0 or newHead >= WIDTH * HEIGHT:
        print("GAME OVER")
        reason = 2
        break
    elif apple == None:
        print("ERROR - No space for new apple")
        reason = 4
        break

    snake.append(newHead)
    printBoard(snake, apple)

# Add any remaining moves
if current_segment:
    segments.append(''.join(current_segment))

# --- Build Replay JSON ---
replay = {
    "version": "5.0",
    "result": {
        "score": score,
        "reason": reason
    },
    "metadata": {
        "map": {"width": WIDTH, "height": HEIGHT},
        "seed": game_seed,
        "initial": {
            "snake": [start, start + 1, start + 2]
        }
    },
    "segments": segments
}

# --- Save to File ---
ReplayHandler().encode_to_binary(replay, "replays/replay_" + str(game_seed) + ".bin")
