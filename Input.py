from abc import ABC, abstractmethod

class Input(ABC):
    state = {}
    newApple = False

    @abstractmethod
    def getInput(self) -> str:
        '''
        Returns the next list of inputs.

        Valid inputs are: quit/state/print and directions like w,a,s,d
        '''
        pass

    def updateState(self, state):
        self.state = state
        pass

    def updateApple(self, apple):
        self.state["apple"] = apple
        self.newApple = True
        pass

class Player(Input):
    def __init__(self):
        pass

    def getInput(self):
        command = input("Enter command (quit/state/print) or movements (w/a/s/d): ")
        return command.strip()
    
class Bot(Input):
    def __init__(self):
        pass

    def getInput(self):
        pass

    def updateState(self, state):
        return super().updateState(state)

class Replay(Input):
    from ReplayHandler import ReplayHandler
    handler = ReplayHandler()
    decoded = {}
    dir = "d"   # Right

    def __init__(self):
        path = input("Enter replay file (.bin): ").strip()
        self.decoded = self.handler.decode_to_dict(path)

        self.state["width"] = self.decoded["metadata"]["map"]["width"]
        self.state["height"] = self.decoded["metadata"]["map"]["height"]
        self.state["seed"] = self.decoded["metadata"]["seed"]
        self.state["snake"] = self.decoded["metadata"]["initial"]["snake"]
        pass

    def convertToDir(self, segment: str) -> str:
        new_segment = ""
        for move in segment:
            if move == 'S':
                new_segment += self.dir
            elif move == 'L':
                if self.dir == 'w': self.dir = 'a'
                elif self.dir == 'a': self.dir = 's'
                elif self.dir == 's': self.dir = 'd'
                elif self.dir == 'd': self.dir = 'w'
                new_segment += self.dir
            elif move == 'R':
                if self.dir == 'w': self.dir = 'd'
                elif self.dir == 'd': self.dir = 's'
                elif self.dir == 's': self.dir = 'a'
                elif self.dir == 'a': self.dir = 'w'
                new_segment += self.dir

        return new_segment

    def getInput(self):
        segment = self.decoded["segments"].pop(0)
        print(segment)
        segment = self.convertToDir(segment)
        print(f"movement played: {segment}")
        return segment