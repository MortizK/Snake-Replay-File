import json
from typing import List, Tuple

# --- Core Data Classes ---
class SnakeReplay:
    def __init__(self, width: int, height: int, snake: List[Tuple[int,int]], direction: str):
        self.replay = {
            "version": "3.0",
            "metadata": {
                "map": {"width": width, "height": height},
                "initial": {"snake": snake, "direction": direction}
            },
            "segments": [],
            "result": {}
        }

    def add_segment(self, apple: Tuple[int,int], moves: List[str], length: int):
        self.replay["segments"].append({
            "apple": list(apple),
            "moves": moves,
            "length": length
        })

    def set_result(self, score: int, reason: str):
        self.replay["result"] = {"score": score, "reason": reason}

    def save_json(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.replay, f, indent=2)

    @staticmethod
    def load_json(path: str):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


# --- Example usage ---
if __name__ == "__main__":
    # Create a new replay
    rep = SnakeReplay(width=20, height=20, snake=[(10,10),(9,10),(8,10)], direction="R")

    # Add 3 apple segments
    rep.add_segment((15,5), ["R","R","R","U","U","L"], length=4)
    rep.add_segment((3,3), ["U","U","L","L","D","D","R"], length=5)
    rep.add_segment((10,10), ["R","R","R","D","L","L","U"], length=6)

    rep.set_result(score=6, reason="collision_with_self")

    # Save replay
    rep.save_json("snake_replay.json")

    # Load replay
    replay_data = SnakeReplay.load_json("snake_replay.json")
    print("Loaded replay with", len(replay_data["segments"]), "segments.")
