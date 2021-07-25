from abc import ABC, abstractmethod
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import IntEnum
from functools import reduce, lru_cache
from itertools import chain
from operator import ior
from typing import Union, NamedTuple, Generator, Dict

from .constants import (
    INFINITY,
    MIN_SQUARE,
    MAX_SQUARE,
    MAX_INT,
    STARTING_FEN,
)
from .utils import bitscan_forward


class _Bitboard(int):
    def hexstring(self):
        return hex(self)

    def __invert__(self):
        return _Bitboard(MAX_INT ^ self)

    def __and__(self, other):
        return _Bitboard(int(other).__and__(self))

    def __rand__(self, other):
        return _Bitboard(int(other).__and__(self))

    def __xor__(self, other):
        return _Bitboard(int(other).__xor__(self))

    def __rxor__(self, other):
        return _Bitboard(int(other).__xor__(self))

    def __or__(self, other):
        return _Bitboard(int(other).__or__(self))

    def __ror__(self, other):
        return _Bitboard(int(other).__or__(self))

    def __repr__(self):
        n = 8
        b = format(self, "064b")
        f = lambda c: " . " if c == "0" else " * "
        return "\n\n".join(
            [" ".join(map(f, b[i : i + n][::-1])) for i in range(0, len(b), n)]
        )

    def __str__(self):
        return repr(self)


Bitboard = lambda v: _Bitboard(v) & MAX_INT


EMPTY = Bitboard(0)
UNIVERSE = Bitboard(MAX_INT)
DIRECTIONS = [8, 1, -8, -1, 7, 9, -7, -9]


class _BitboardMixin(int):
    _value_ = 0

    @property
    def bitboard(self) -> Bitboard:
        return Bitboard(1 << self._value_)


class Square(_BitboardMixin):
    def __new__(cls, value):
        assert value >= MIN_SQUARE and value <= MAX_SQUARE
        return super().__new__(cls, value)

    @property
    def bitboard(self) -> Bitboard:
        return Bitboard(1 << self)


class AutoIncrementingEnum(IntEnum):
    def __new__(cls, *args):
        value = len(cls.__members__)
        obj = int.__new__(cls)
        obj._value_ = int(value)
        return obj


class SquareEnum(AutoIncrementingEnum):
    def __new__(cls, *args):
        value = len(cls.__members__)
        obj = int.__new__(cls)
        obj._value_ = Square(value)
        return obj


class PieceType(IntEnum):
    """3-bit representation of pieces."""

    NULL = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6
    ENPASSANT = 7


class Color(IntEnum):
    WHITE = 0
    BLACK = 1

    def __invert__(self):
        return Color.WHITE if self else Color.BLACK


class Squares(SquareEnum):
    """Squares by their algebraic notation name."""

    A1 = "a1"
    B1 = "b1"
    C1 = "c1"
    D1 = "d1"
    E1 = "e1"
    F1 = "f1"
    G1 = "g1"
    H1 = "h1"

    A2 = "a2"
    B2 = "b2"
    C2 = "c2"
    D2 = "d2"
    E2 = "e2"
    F2 = "f2"
    G2 = "g2"
    H2 = "h2"

    A3 = "a3"
    B3 = "b3"
    C3 = "c3"
    D3 = "d3"
    E3 = "e3"
    F3 = "f3"
    G3 = "g3"
    H3 = "h3"

    A4 = "a4"
    B4 = "b4"
    C4 = "c4"
    D4 = "d4"
    E4 = "e4"
    F4 = "f4"
    G4 = "g4"
    H4 = "h4"

    A5 = "a5"
    B5 = "b5"
    C5 = "c5"
    D5 = "d5"
    E5 = "e5"
    F5 = "f5"
    G5 = "g5"
    H5 = "h5"

    A6 = "a6"
    B6 = "b6"
    C6 = "c6"
    D6 = "d6"
    E6 = "e6"
    F6 = "f6"
    G6 = "g6"
    H6 = "h6"

    A7 = "a7"
    B7 = "b7"
    C7 = "c7"
    D7 = "d7"
    E7 = "e7"
    F7 = "f7"
    G7 = "g7"
    H7 = "h7"

    A8 = "a8"
    B8 = "b8"
    C8 = "c8"
    D8 = "d8"
    E8 = "e8"
    F8 = "f8"
    G8 = "g8"
    H8 = "h8"

    @property
    def bitboard(self) -> Bitboard:
        return Bitboard(1 << self._value_)


class Ranks:
    """Ranks from white perspective"""

    RANK_1 = Bitboard(
        Squares.A1.bitboard
        | Squares.B1.bitboard
        | Squares.C1.bitboard
        | Squares.D1.bitboard
        | Squares.E1.bitboard
        | Squares.F1.bitboard
        | Squares.G1.bitboard
        | Squares.H1.bitboard
    )
    RANK_2 = Bitboard(RANK_1 << 8)
    RANK_3 = Bitboard(RANK_2 << 8)
    RANK_4 = Bitboard(RANK_3 << 8)
    RANK_5 = Bitboard(RANK_4 << 8)
    RANK_6 = Bitboard(RANK_5 << 8)
    RANK_7 = Bitboard(RANK_6 << 8)
    RANK_8 = Bitboard(RANK_7 << 8)


class Files:
    A = Bitboard(reduce(ior, (getattr(Squares, f"A{i}").bitboard for i in range(1, 9))))
    B = Bitboard(reduce(ior, (getattr(Squares, f"B{i}").bitboard for i in range(1, 9))))
    C = Bitboard(reduce(ior, (getattr(Squares, f"C{i}").bitboard for i in range(1, 9))))
    D = Bitboard(reduce(ior, (getattr(Squares, f"D{i}").bitboard for i in range(1, 9))))
    E = Bitboard(reduce(ior, (getattr(Squares, f"E{i}").bitboard for i in range(1, 9))))
    F = Bitboard(reduce(ior, (getattr(Squares, f"F{i}").bitboard for i in range(1, 9))))
    G = Bitboard(reduce(ior, (getattr(Squares, f"G{i}").bitboard for i in range(1, 9))))
    H = Bitboard(reduce(ior, (getattr(Squares, f"H{i}").bitboard for i in range(1, 9))))


SQUARES = {i: Squares[square] for i, square in enumerate(Squares.__members__)}
RANKS = {i: getattr(Ranks, f"RANK_{i + 1}") for i in range(8)}
FILES = {i: getattr(Files, c.upper()) for i, c in enumerate("abcdefgh")}
COLORS = {
    0: Color.WHITE,
    1: Color.BLACK,
}
PIECE_TYPE_MAP = {
    "p": PieceType.PAWN,
    "n": PieceType.KNIGHT,
    "b": PieceType.BISHOP,
    "r": PieceType.ROOK,
    "q": PieceType.QUEEN,
    "k": PieceType.KING,
    "ep": PieceType.ENPASSANT,
    "__default__": "Piece",
}
INV_PIECE_TYPE_MAP = {v: k for k, v in PIECE_TYPE_MAP.items()}
PIECE_SYMBOL_MAP = {
    (PieceType.ENPASSANT, Color.WHITE): "^",
    (PieceType.ENPASSANT, Color.BLACK): "v",
    (PieceType.PAWN, Color.WHITE): "♙",
    (PieceType.PAWN, Color.BLACK): "♟︎",
    (PieceType.KNIGHT, Color.WHITE): "♘",
    (PieceType.KNIGHT, Color.BLACK): "♞",
    (PieceType.BISHOP, Color.WHITE): "♗",
    (PieceType.BISHOP, Color.BLACK): "♝",
    (PieceType.ROOK, Color.WHITE): "♖",
    (PieceType.ROOK, Color.BLACK): "♜",
    (PieceType.QUEEN, Color.WHITE): "♕",
    (PieceType.QUEEN, Color.BLACK): "♛",
    (PieceType.KING, Color.WHITE): "♔",
    (PieceType.KING, Color.BLACK): "♚",
}
PROMOTABLE = {PieceType.KNIGHT, PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN}
CAN_CHECK = {
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.ROOK,
    PieceType.QUEEN,
    PieceType.PAWN,
}
MOVABLE = {
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.ROOK,
    PieceType.QUEEN,
    PieceType.PAWN,
    PieceType.KING,
}
ATTACKERS = {
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.ROOK,
    PieceType.QUEEN,
    PieceType.PAWN,
    PieceType.KING,
}
UNBLOCKABLE_CHECKERS = {PieceType.KNIGHT, PieceType.PAWN}
SLIDERS = {PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN}
XRAYS = {PieceType.PAWN, PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN}

PIECE_REGISTRY = {}


class AbstractPiece(ABC):
    _type: PieceType = None

    def __init__(self, color: Color):
        self.color = color
        self.zobrist_index = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        PIECE_REGISTRY[cls._type] = cls
        PIECE_REGISTRY[INV_PIECE_TYPE_MAP.get(cls._type or "__default__")] = cls

    @abstractmethod
    def captures(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def quiet_moves(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def pseudo_legal_moves(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def legal_moves(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def legal_captures(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def legal_quiet(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def attack_set(self, *args, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        return PIECE_SYMBOL_MAP[(self._type, 1 - self.color)]


class CastlingRightsEnum(AutoIncrementingEnum):
    none = "-"
    K = "K"
    Q = "Q"
    KQ = "KQ"
    k = "k"
    Kk = "Kk"
    Qk = "Qk"
    KQk = "KQk"
    q = "q"
    Kq = "Kq"
    Qq = "Qq"
    KQq = "KQq"
    kq = "kq"
    Kkq = "Kkq"
    Qkq = "Qkq"
    KQkq = "KQkq"


class CastlingRights(int):
    """
    Representation of Castling Rights as a 4-bit number

    where 1 = castling is permitted.

    0 0 0 0
    │ │ │ |_ w kingside
    │ │ │___ w queenside
    │ │_____ b kingside
    │_______ b queenside

    """

    def __new__(cls, value):
        assert value >= 0 and value <= 15
        return super().__new__(cls, value)

    def __and__(self, other):
        return self.__class__(int(self) & int(other))

    def __rand__(self, other):
        return self.__class__(int(self) & int(other))

    def __xor__(self, other):
        return self.__class__(int(self) ^ int(other))

    def __rxor__(self, other):
        return self.__class__(int(self) ^ int(other))

    def __or__(self, other):
        return self.__class__(int(self) | int(other))

    def __ror__(self, other):
        return self.__class__(int(self) | int(other))

    def __repr__(self) -> str:
        cr = CastlingRightsEnum(self)
        return f"<CastlingRights {cr.name}={cr._value_}>"

    def __str__(self) -> str:
        return CastlingRightsEnum(self).name if self else "-"

    def __getitem__(self, c: Color) -> int:
        if c == Color.WHITE:
            return self & 3
        return self >> 2


SubState = NamedTuple(
    "Substate",
    [
        ("castling", CastlingRights),
        ("captured", AbstractPiece),
        ("ep", Square),
        ("move", "Move"),
        ("fen", str),
    ],
)


class State:
    def __init__(
        self,
        turn: Color = Color.WHITE,
        castling_rights: str = "KQkq",
        ep_square: str = None,
        half_move_clock: int = 0,
        full_move_clock: int = 0,
        move=None,
        fen=None,
    ):
        ep_square = (
            Square(Squares[ep_square.upper()]._value_)
            if ep_square not in ("-", None)
            else None
        )
        castling_rights = castling_rights if castling_rights != "-" else "none"
        castling_rights = CastlingRights(CastlingRightsEnum[castling_rights]._value_)

        self.half_move_clock = int(half_move_clock)
        self.full_move_clock = int(full_move_clock)
        self.turn = Color.WHITE if turn in ("w", 0) else Color.BLACK
        self.__stack = deque(
            [SubState(castling=castling_rights, captured=None, ep=ep_square, move=move, fen=fen)]
        )

    def __iter__(self):
        return reversed(self.__stack)

    @staticmethod
    def __update_castling_rights(prev, current):
        intersect = prev & current
        return (prev ^ intersect) if intersect else prev

    def push(self, captured=None, castling=None, ep_square=None, move=None, fen=None):
        self.full_move_clock += 1
        self.turn = ~self.turn
        cur = self.__stack[0]
        # print("Castling state: ", cur.castling)
        # print("Castling state toggle: ", castling)
        # input()
        _s = SubState(
            castling=self.__update_castling_rights(cur.castling, castling),
            captured=captured,
            ep=ep_square,
            move=move,
            fen=fen
        )
        self.__stack.appendleft(_s)

    def pop(self):
        self.full_move_clock -= 1
        self.turn = ~self.turn
        if self.__stack:
            return self.__stack.popleft()
        return (CastlingRights(15), None, None)

    def top(self):
        return self.__stack[0]

    @property
    def castling_rights(self):
        return self.__stack[0].castling

    @property
    def ep_square(self):
        return self.__stack[0].ep

    @property
    def ply(self):
        return self.full_move_clock

    @property
    def fen_suffix(self) -> str:
        eps = self.ep_square
        return " ".join(
            str(v)
            for v in (
                self.turn.name[0].lower(),
                str(self.castling_rights),
                SQUARES[eps].name.lower() if eps is not None else "-",
                self.half_move_clock,
                self.full_move_clock,
            )
        )

PieceAndSquare = NamedTuple("PieceAndSquare", [("piece", AbstractPiece), ("square", Square)])

class NodeType(IntEnum):
    EXACT = 0
    ALPHA = 1
    BETA = 2

@dataclass
class SearchResult:
    ply: int
    score: float
    move: "Move" = None
    alpha: float = -INFINITY
    beta: float = INFINITY
    nodetype: NodeType = None