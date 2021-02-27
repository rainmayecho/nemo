from abc import ABC, abstractmethod
from enum import IntEnum
from functools import reduce
from itertools import chain
from operator import ior
from typing import Union

from .constants import MIN_SQUARE, MAX_SQUARE, MAX_INT, STARTING_FEN


class Bitboard(int):
    def __new__(cls, value):
        return super().__new__(cls, value & MAX_INT)

    def __invert__(self):
        return self.__class__(MAX_INT ^ self)

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

    def __repr__(self):
        n = 8
        b = format(self, "064b")
        f = lambda c: " . " if c == "0" else " * "
        return "\n\n".join([" ".join(map(f, b[i : i + n][::-1])) for i in range(0, len(b), n)])

    def __str__(self):
        return repr(self)


EMPTY = Bitboard(0)
UNIVERSE = Bitboard(MAX_INT)
DIRECTIONS = [8, 1, -8, -1, 7, 9, -7, -9]


class Square(int):
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
        obj._value_ = Square(value)
        return obj

    @property
    def bitboard(self) -> Bitboard:
        return Bitboard(1 << self._value_)


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


class Squares(AutoIncrementingEnum):
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

PIECE_REGISTRY = {}

class Piece(ABC):
    _type: PieceType = None

    def __init__(self, color: Color):
        self.color = color

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        PIECE_REGISTRY[INV_PIECE_TYPE_MAP[cls._type]] = cls

    @abstractmethod
    def captures(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def quiet_moves(self, *args, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        return PIECE_SYMBOL_MAP[(self._type, 1 - self.color)]


class StackedBitboard:
    def __init__(self, bitboards_by_color_and_type, square_occupancy):
        self.__boards = bitboards_by_color_and_type
        self.__square_occupancy = square_occupancy

    @property
    def white_occupancy(self):
        occ = Bitboard(EMPTY)
        for bb in self.__boards[Color.WHITE].values():
            occ |= bb
        return occ

    @property
    def black_occupancy(self):
        occ = Bitboard(EMPTY)
        for bb in self.__boards[Color.BLACK].values():
            occ |= bb
        return occ

    @property
    def occupancy(self):
        return self.white_occupancy | self.black_occupancy

    @property
    def squares(self):
        return self.__square_occupancy

    @property
    def boards(self):
        return self.__boards

    def piece_at(s: int) -> "Piece":
        return self.squares[s]

    def board_for(self, p: "Piece") -> Bitboard:
        return self.__boards[p.color][p._type]

    def place_piece(s: "Square", p: "Piece") -> None:
        if not isinstance(s, Square):
            s = Square(s)

        existing_piece_at_s = self.piece_at(s)
        placing_piece_bb = self.board_for(p)
        if existing_piece_at_s is not None:
            existing_piece_bb = self.board_for(existing_piece_at_s)
            placing_piece_bb = self.board_for(p)
            existing_piece_bb ^= s.bitboard  # Unset the bit for the existing piece
        placing_piece_bb ^= s.bitboard  # Set the bit for the new piece
        self.square[s] = p

    def remove_piece(s: "Square") -> None:
        if not isinstance(s, Square):
            s = Square(s)
        existing_piece_at_s = self.piece_at(s)
        if existing_piece_at_s is not None:
            existing_piece_bb = self.get_board_for(existing_piece_at_s)
            existing_piece_bb ^= s.bitboard  # Unset the bit for the existing piece
        self.square[s] = None

    def __getitem__(self, key):
        if isinstance(key, Color):
            return getattr(self, f"{key.name.lower()}_occupancy")
        elif isinstance(key, Piece):
            return self.board_for(key)
        elif isinstance(key, (Square, int)):
            return self.squares[key]
        else:
            raise TypeError("unsupported type for lookup")

    def __hash__(self):
        return hash(tuple(self.squares))



class CastlingRights(int):
    MAPPING = {
        0: "-",
        1: "k",
        2: "q",
        3: "kq",
    }

    def __init__(self, w: int = 3, b: int = 3):
        self.white = 3
        self.black = 3

    def __and__(self, rook_square: Square):
        if rook_square == Squares.A1:
            return bool(self.white & 2)
        elif rook_square == Squares.H1:
            return bool(self.white & 1)
        elif rook_square == Squares.H8:
            return bool(self.black & 1)
        elif rook_square == Squares.A8:
            return bool(self.black & 2)

    def king_moved(self, color: Color):
        setattr(self, color.name.lower(), 0)

    def rook_moved(self, from_square: Square):
        if from_square == Squares.A1:
            self.white ^= 2
        elif from_square == Squares.H1:
            self.white ^= 1
        elif from_square == Squares.A8:
            self.black ^= 2
        elif from_square == Squares.H8:
            self.black ^= 1

    def copy(self) -> "CastlingRights":
        return type(self)(self.white, self.black)

    def __str__(self) -> str:
        wcr = self.MAPPING[self.white].upper()
        bcr = self.MAPPING[self.black].upper()
        return "-" if wcr == bcr else wcr + bcr


class State:
    def __init__(
        self,
        turn: Color = Color.WHITE,
        castling_rights: CastlingRights = None,
        ep_square: str = None,
        half_move_clock: int = 0,
        full_move_clock: int = 0,
        prev: "State" = None,
    ):
        self.castling_rights = castling_rights or CastlingRights()
        self.ep_square = Squares[ep_square.upper()] if ep_square not in ("-", None) else None
        self.half_move_clock = half_move_clock
        self.full_move_clock = full_move_clock
        self.turn = Color.WHITE
        self.prev = prev

    def __next__(self):
        return type(self)(
            COLORS[self.turn ^ 1],
            self.castling_rights.copy(),
            0,
            self.full_move_clock + 1,
            self,
        )

    @property
    def fen_suffix(self) -> str:
        c, ep, cr, hmc, fmc = (
            self.turn.name[0].lower(),
            str(self.castling_rights),
            self.ep_square.name.lower(),
            self.half_move_clock,
            self.full_move_clock,
        )
        return f"{c} {ep or '-'} {cr} {hmc} {fmc}"
