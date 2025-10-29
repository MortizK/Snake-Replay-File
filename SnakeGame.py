import json
from random import choice

# --- Settings ---
WIDTH = 8
HEIGHT = 8

UP = "w"
LEFT = "a"
DOWN = "s"
RIGHT = "d"
DIRECTIONS = [UP, LEFT, DOWN, RIGHT]

# --- Helper functions ---
def cordToID(x, y) -> int:
    return y * WIDTH + x

def idToCord(id) -> list[int]:
    y = id // HEIGHT
    x = id % HEIGHT
    return [x, y]

def printBoard(snake, apple):
    string = ""
    for i in range(WIDTH * HEIGHT):
        if i % HEIGHT == 0:
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
        print("WARNING: No free space for new apple!")
        return None  # No free space left, game should end
    return choice(free_cells)


# --- Game Initialization ---
start_index = (HEIGHT // 2) * WIDTH
snake = [start_index, start_index + 1, start_index + 2]
apple = start_index + WIDTH - 1

printBoard(snake, apple)

# --- Replay setup ---
replay = {
    "version": "3.0",
    "metadata": {
        "map": {"width": WIDTH, "height": HEIGHT},
        "initial": {"snake": [idToCord(i) for i in snake], "direction": "d"}
    },
    "segments": []
}

segment_moves = []
segment_start_apple = idToCord(apple)

# --- Game loop ---
while True:
    # Input Handling
    dir = input().lower().strip()
    while dir not in DIRECTIONS:
        dir = input().lower().strip()

    # Movement Direction
    newHead = None
    if dir == UP:
        newHead = snake[-1] - HEIGHT
    elif dir == LEFT:
        newHead = snake[-1] - 1
    elif dir == DOWN:
        newHead = snake[-1] + HEIGHT
    elif dir == RIGHT:
        newHead = snake[-1] + 1

    # Record move
    segment_moves.append(dir)

    # Update movement & apple
    ate_apple = newHead == apple
    if ate_apple:
        apple = newApple(snake, newHead)
    else:
        snake.pop(0)

    # Move head
    snake.append(newHead)

    # Game Ending Conditions
    if len(snake) == HEIGHT * WIDTH:
        print("YOU WIN")
        result = {"score": len(snake), "reason": "win"}
        break
    elif apple is None:
        print("ERROR: No space for new apple.")
        result = {"score": len(snake), "reason": "error"}
        break
    elif newHead in snake:
        print("GAME OVER")
        result = {"score": len(snake), "reason": "collision"}
        break

    # Draw
    printBoard(snake, apple)

    # If apple eaten, close segment and start a new one
    if ate_apple:
        replay["segments"].append({
            "apple": segment_start_apple,
            "moves": segment_moves,
            "length": len(snake)
        })
        segment_moves = []
        segment_start_apple = idToCord(apple)

# --- After game ends ---
# Add final segment if there were leftover moves
if segment_moves:
    replay["segments"].append({
        "apple": segment_start_apple,
        "moves": segment_moves,
        "length": len(snake)
    })

replay["result"] = result

# --- Save Replay ---
with open("snake_replay.json", "w", encoding="utf-8") as f:
    json.dump(replay, f, indent=2)

print("\nReplay saved to snake_replay.json")
