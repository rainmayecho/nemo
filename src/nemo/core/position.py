from collections import defaultdict

from .constants import STARTING_FEN
from .types import BitBoard, Color, Piece, PIECE_TYPE_MAP, Square, State
from .move import Move


class Position:
    def __init__(self, fen=STARTING_FEN):
        self.clear()
        if fen is not None:
            self.from_fen(fen)

    def clear(self):
        self.__square_occupancy = [None] * 64
        self.__color_occupancy_bb = BitBoard(0)
        self.__boards = defaultdict(lambda: defaultdict(BitBoard))
        self.state = None

    def from_fen(self, fen):
        ranks, turn, castling_rights, ep_square, hmc, fmc = fen.split(" ")
        i = 0
        rows = ranks.split("/")[::-1]
        for i, row in enumerate(rows):
            j = 0
            for c in row:
                if not c.isdigit():
                    color = Color.WHITE if c.isupper() else Color.BLACK
                    piece = Piece(PIECE_TYPE_MAP[c.lower()], color)
                    idx = i * 8 + j
                    bb = 1 << idx
                    self.__square_occupancy[idx] = piece
                    self.__color_occupancy_bb |= bb
                    self.__boards[color][piece._type] = bb
                    j += 1
                else:
                    j += int(c)
        self.state = State(
            turn,
            castling_rights,
            ep_square,
            hmc,
            fmc,
        )

    def make_move(self, move: Move) -> None:
        return

    def unmake_move(self, move: Move) -> None:
        return

    @property
    def squares(self):
        return self.__square_occupancy

    def __str__(self):
        div = "┼" + "───┼" * 8
        rows = [div]
        for i in range(8):
            row = []
            for j in range(8):
                idx = i * 8 + j
                p = self.__square_occupancy[idx]
                row.append(p or " ")
            rows.append("│ " + f" │ ".join(str(p) for p in row) + " │")
            rows.append(div)
        return "\n".join(rows[::-1])
