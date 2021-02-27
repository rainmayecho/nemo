from collections import defaultdict

from .constants import STARTING_FEN
from .piece import Piece
from .types import Bitboard, Color, PIECE_REGISTRY, Square, Squares, StackedBitboard, State
from .move import Move


class Position:
    def __init__(self, fen=STARTING_FEN):
        self.clear()
        if fen is not None:
            self.from_fen(fen)

    def clear(self):
        self.__boards = None
        self.__state = None

    def from_fen(self, fen):
        ranks, turn, castling_rights, ep_square, hmc, fmc = fen.split(" ")
        i = 0
        rows = ranks.split("/")[::-1]
        boards = defaultdict(lambda: defaultdict(lambda: Bitboard(0)))
        square_occupancy = [None] * 64

        if ep_square != "-":
            square = Squares[ep_square.upper()]
            c = Color.WHITE if square._value_ < 32 else Color.BLACK
            piece = PIECE_REGISTRY["ep"](c)
            boards[c][piece._type] |= square.bitboard
            square_occupancy[square._value_] = piece

        for i, row in enumerate(rows):
            j = 0
            for c in row:
                if not c.isdigit():
                    color = Color.WHITE if c.isupper() else Color.BLACK
                    piece = PIECE_REGISTRY[c.lower()](color)
                    idx = i * 8 + j
                    bb = boards[color][piece._type] | (1 << idx)
                    square_occupancy[idx] = piece
                    boards[color][piece._type] = bb
                    j += 1
                else:
                    j += int(c)

        self.__boards = StackedBitboard(boards, square_occupancy)
        self.__state = State(
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
        return self.__boards.squares

    @property
    def bitboards(self):
        return self.__boards

    def __str__(self):
        div = "┼" + "───┼" * 8
        rows = [div]
        for i in range(8):
            row = []
            for j in range(8):
                idx = i * 8 + j
                p = self.__boards.squares[idx]
                row.append(p or " ")
            rows.append("│ " + f" │ ".join(str(p) for p in row) + " │")
            rows.append(div)
        return "\n".join(rows[::-1])


def test_positions():
    white_pawn = PIECE_REGISTRY["p"](Color.WHITE)
    black_pawn = PIECE_REGISTRY["p"](Color.BLACK)

    p = Position()
    assert white_pawn.captures(p.bitboards) == []
    assert len(white_pawn.quiet_moves(p.bitboards)) == 16

    p = Position(fen="rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    assert len(white_pawn.captures(p.bitboards)) == 1
    assert str(white_pawn.captures(p.bitboards)[0]) == "e4d5"
    assert len(black_pawn.captures(p.bitboards)) == 1
    assert str(white_pawn.captures(p.bitboards)[0]) == "d5e4"

    p = Position(fen="rnbqkbnr/1pp1pppp/p7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3")
    assert len(white_pawn.captures(p.bitboards)) == 1
    assert len(black_pawn.captures(p.bitboards)) == 0

    p = Position(fen="rnbqkbnr/1pppppPp/8/8/8/8/PpPPP1PP/RNBQKBNR w KQkq - 0 5")
    assert len(white_pawn.captures(p.bitboards)) == 8
    assert len(black_pawn.captures(p.bitboards)) == 8
    assert white_pawn.captures(p.bitboards)[0].is_promotion
    assert black_pawn.captures(p.bitboards)[0].is_promotion



