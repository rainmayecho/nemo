from .constants import STARTING_FEN
from .position import Position
from .pgn import PGNWriter


class Game:
    def __init__(self, position=None, fen=STARTING_FEN):
        if position is None:
            self.position = Position(fen=fen)
        else:
            self.position = position
        self.pgn_writer = PGNWriter(position=self.position)

    @property
    def pgn(self):
        return self.pgn_writer.write()
