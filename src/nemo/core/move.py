from enum import IntEnum
from .types import Square, SQUARES, Squares, CastlingRights, PieceType, INV_PIECE_TYPE_MAP


class MoveFlags(IntEnum):
    QUIET = 0
    DOUBLE_PAWN_PUSH = 1
    KINGSIDE_CASTLE = 2
    QUEENSIDE_CASTLE = 3
    CAPTURES = 4
    ENPASSANT_CAPTURE = 5
    ILLEGAL = 6
    ILLEGAL_2 = 7
    PROMOTION = 8
    PROMOTION_N = 8
    PROMOTION_B = 9
    PROMOTION_R = 10
    PROMOTION_Q = 11
    PROMOTION_N_CAPTURE = 12
    PROMOTION_B_CAPTURE = 13
    PROMOTION_R_CAPTURE = 14
    PROMOTION_Q_CAPTURE = 15


class Move:
    def __init__(self, _from: int = 0, _to: int = 0, flags: int = 0, uci: str = None, _move : int = None):
        if _move is not None:
            self._move = _move
            self._flags = _move >> 12
        else:
            if uci is not None:
                _from = Squares[uci[0:2].upper()]._value_
                _to = Squares[uci[2:4].upper()]._value_
            else:
                _from = SQUARES[_from]._value_
                _to = SQUARES[_to]._value_
            self._flags = flags
            self._move = (flags << 12) | ((_from & 63) << 6) | (_to & 63)

    @property
    def castling_rights_premask(self) -> int:
        if self.flags == MoveFlags.QUEENSIDE_CASTLE:
            return 2
        elif self.flags == MoveFlags.KINGSIDE_CASTLE:
            return 1
        return 0

    @property
    def is_castle_kingside(self) -> int:
        return self.flags == MoveFlags.KINGSIDE_CASTLE

    @property
    def is_castle_queenside(self) -> int:
        return self.flags == MoveFlags.QUEENSIDE_CASTLE

    @property
    def ep_square_premask(self):
        if self.flags == MoveFlags.DOUBLE_PAWN_PUSH:
            return self._to
        return None

    @property
    def is_enpassant_capture(self):
        return self.flags == MoveFlags.ENPASSANT_CAPTURE

    @property
    def is_double_pawn_push(self):
        return self.flags == MoveFlags.DOUBLE_PAWN_PUSH

    @property
    def is_quiet(self):
        return self.flags == MoveFlags.QUIET

    @property
    def is_capture(self):
        return self.flags & MoveFlags.CAPTURES

    @property
    def is_promotion(self):
        return self.flags & MoveFlags.PROMOTION

    @property
    def promotion_piece_type(self):
        if not self.is_promotion:
            return None
        if self._flags in (MoveFlags.PROMOTION, MoveFlags.PROMOTION_N_CAPTURE):
            return PieceType.KNIGHT
        elif self._flags in (MoveFlags.PROMOTION_Q, MoveFlags.PROMOTION_Q_CAPTURE):
            return PieceType.QUEEN
        elif self._flags in (MoveFlags.PROMOTION_R, MoveFlags.PROMOTION_R_CAPTURE):
            return PieceType.ROOK
        elif self._flags in (MoveFlags.PROMOTION_B, MoveFlags.PROMOTION_B_CAPTURE):
            return PieceType.BISHOP

    @property
    def promotion_suffix(self):
        return f"={INV_PIECE_TYPE_MAP.get(self.promotion_piece_type, '')}" if self.promotion_piece_type else ""

    @property
    def _to(self):
        return self._move & 63

    @property
    def _from(self):
        return (self._move >> 6) & 63

    @property
    def flags(self):
        return self._flags

    @property
    def uci(self) -> str:
        return str(self)


    @property
    def san_suffix(self) -> str:
        capture = "x" if self.is_capture else ""
        return f"{capture}{Squares(self._to).name.lower()}{self.promotion_suffix}"

    def __iter__(self):
        yield Square(self._from)
        yield Square(self._to)

    def __invert__(self) -> "Move":
        return self.__class__(self._to, self._from, self.flags)

    def __repr__(self) -> str:
        return f"<Move {SQUARES[self._from].name.lower()} to {SQUARES[self._to].name.lower()} flags={self.flags}>"

    def __str__(self) -> str:
        return f"{SQUARES[self._from].name.lower()}{SQUARES[self._to].name.lower()}{self.promotion_suffix}"

    def __hash__(self) -> int:
        return hash(self._move)

class MoveList:
    """Encapsulates ordering a sequence of candidate moves"""

    def __init__(self, moves):
        self.__moves = moves

    def __add__(self, *moves):
        self.__moves = [*self.__moves, *moves]

    def __iter__(self):
        return self

    def __next__(self):
        return iter(self)

    def sort(self):
        pass
