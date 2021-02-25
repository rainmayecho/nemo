from enum import IntEnum
from .types import SQUARES, Squares


class MoveFlags(IntEnum):
    QUIET = 0
    DOUBLE_PAWN_PUSH = 1
    KINGSIDE_CASTLE = 2
    QUEENSIDE_CASTLE = 3
    CAPTURES = 4
    ENPASSANT_CAPTURE = 5
    PROMOTION = 8
    PROMOTION_N = 8
    PROMOTION_B = 9
    PROMOTION_R = 10
    PROMOTION_Q = 11
    PROMOTION_N_CAPTURE = 8
    PROMOTION_B_CAPTURE = 9
    PROMOTION_R_CAPTURE = 10
    PROMOTION_Q_CAPTURE = 11


class Move:
    def __init__(self, _from: int = 0, _to: int = 0, flags: int = 0, uci: str = None):
        if uci is not None:
            _from = Squares[uci[0:2].upper()]
            _to = Squares[uci[2:4].upper()]
        else:
            _from = SQUARES[_from]
            _to = SQUARES[_to]
        self._move = (flags << 12) | ((_from & 63) << 6) | (_to & 63)

    @property
    def is_quiet(self):
        return self._move == MoveFlags.QUIET

    @property
    def is_capture(self):
        return self._move & MoveFlags.CAPTURE

    @property
    def is_promotion(self):
        return self._move & MoveFlags.PROMOTION

    @property
    def _to(self):
        return self._move & 63

    @property
    def _from(self):
        return (self._move >> 6) & 63

    @property
    def flags(self):
        return (self._move >> 12) & 15

    @property
    def uci(self) -> str:
        return str(self)

    def __invert__(self) -> "Move":
        return self.__class__(self._to, self._from, self.flags)

    def __repr__(self) -> str:
        return f"<Move {SQUARES[self._from].name.lower()} to {SQUARES[self._to].name.lower()}>"

    def __str__(self) -> str:
        return f"{SQUARES[self._from].name.lower()}{SQUARES[self._to].name.lower()}"
