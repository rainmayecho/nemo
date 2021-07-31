
class EngineException(RuntimeError):
    def __init__(self, *args, position: "Position" = None, **kwargs):
        self.position = position

class IllegalMoveException(EngineException):
    pass