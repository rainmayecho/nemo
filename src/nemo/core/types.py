from abc import ABC, abstractmethod
from collections import deque, defaultdict
from enum import IntEnum
from functools import reduce, lru_cache
from itertools import chain
from operator import ior
from typing import Union, NamedTuple, Generator, Dict

from .constants import MIN_SQUARE, MAX_SQUARE, MAX_INT, STARTING_FEN


Bitboard = lambda v: int(v) & MAX_INT
# class Bitboard(int):
#     def __new__(cls, value):
#         return super().__new__(cls, value & MAX_INT)

#     def __invert__(self):
#         return self.__class__(MAX_INT ^ self)

#     def __and__(self, other):
#         return self.__class__(int(self) & int(other))

#     def __rand__(self, other):
#         return self.__class__(int(self) & int(other))

#     def __xor__(self, other):
#         return self.__class__(int(self) ^ int(other))

#     def __rxor__(self, other):
#         return self.__class__(int(self) ^ int(other))

#     def __or__(self, other):
#         return self.__class__(int(self) | int(other))

#     def __ror__(self, other):
#         return self.__class__(int(self) | int(other))

#     def __repr__(self):
#         n = 8
#         b = format(self, "064b")
#         f = lambda c: " . " if c == "0" else " * "
#         return "\n\n".join([" ".join(map(f, b[i : i + n][::-1])) for i in range(0, len(b), n)])

#     def __str__(self):
#         return repr(self)


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
    "__default__": "Piece"
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

PIECE_REGISTRY = {}

class AbstractPiece(ABC):
    _type: PieceType = None

    def __init__(self, color: Color):
        self.color = color

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
    def attack_set(self, *args, **kwargs):
        raise NotImplementedError()


    def __str__(self):
        return PIECE_SYMBOL_MAP[(self._type, 1 - self.color)]


class StackedBitboard:
    def __init__(self, bitboards_by_color_and_type, square_occupancy):
        self.__boards = bitboards_by_color_and_type
        self.__color_occupancy = [
            self.__white_occupancy(),
            self.__black_occupancy(),
        ]
        self.__square_occupancy = square_occupancy
        self.__attack_sets = self.__get_attack_sets()
        self.__checkers_bb = [
            self.__checkers(Color.WHITE),
            self.__checkers(Color.BLACK),
        ]

    @staticmethod
    def test_piece(c: Color, piece_type: PieceType):
        return PIECE_REGISTRY[piece_type](c)


    def __get_attack_sets(self) -> Dict[Color, Dict[PieceType, Bitboard]]:
        attack_sets = {
            Color.WHITE: {}, Color.BLACK: {}
        }
        for c in self.__boards:
            for piece_type, piece_bb in self.__boards[c].items():
                attack_sets[c][piece_type] = self.test_piece(c, piece_type).attack_set(self)
        return attack_sets

    def __checkers(self, c: Color) -> Bitboard:
        """Bitboard representing pieces that can check the King of color `c`"""
        checkers_bb = Bitboard(0)
        king_bb = self.__boards[c][PieceType.KING]
        for piece_type, attack_set in self.__attack_sets[~c].items():
            if attack_set & king_bb:
                checkers_bb |= self.__boards[c][piece_type]
        return checkers_bb

    def king_in_check(self, c: Color):
        king_bb = self.__boards[c][PieceType.KING]
        for piece_type, piece_bb in self.__boards[~c].items():
            if piece_type not in (PieceType.KING, PieceType.ENPASSANT):
                piece = self.test_piece(~c, piece_type)
                # print(piece.attack_set(self) & king_bb)
                if piece.attack_set(self) & king_bb:
                    return True
        return False

    def __white_occupancy(self):
        occ = Bitboard(EMPTY)
        for piece_type, bb in self.__boards[Color.WHITE].items():
            if piece_type != PieceType.ENPASSANT:
                occ |= bb
        return occ

    def __black_occupancy(self):
        occ = Bitboard(EMPTY)
        for piece_type, bb in self.__boards[Color.BLACK].items():
            if piece_type != PieceType.ENPASSANT:
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

    def piece_at(self, s: int) -> "Piece":
        return self.squares[s]

    def board_for(self, p: "Piece") -> Bitboard:
        return self.__boards[p.color][p._type]

    def by_color(self, c: Color) -> Bitboard:
        return self.__color_occupancy[c]

    def king_bb(self, c: Color) -> Bitboard:
        return self.__boards[c][PieceType.KING]

    def place_piece(self, s: "Square", p: "Piece") -> None:
        if not isinstance(s, Square):
            s = Square(s)

        existing_piece_at_s = self.piece_at(s)
        placing_piece_bb = self.board_for(p)
        c = p.color
        s_bb = s.bitboard
        if existing_piece_at_s is not None:
            _type = existing_piece_at_s._type
            self.__boards[~c][_type] ^= s_bb
            self.__color_occupancy[~c] ^= s_bb
            self.__attack_sets[~c][_type] = self.test_piece(c, _type).attack_set(self)
        self.__boards[c][p._type] ^= s_bb  # Set the bit for the new piece
        self.__color_occupancy[c] ^= s_bb
        self.__attack_sets[c][p._type] = self.test_piece(c, p._type).attack_set(self)

        self.squares[s] = p
        return existing_piece_at_s

    def remove_piece(self, s: "Square") -> None:
        if not isinstance(s, Square):
            s = Square(s)
        existing_piece_at_s = self.piece_at(s)
        s_bb = s.bitboard
        if existing_piece_at_s is not None:
            c = existing_piece_at_s.color
            _type = existing_piece_at_s._type
            self.__boards[c][_type] ^= s_bb
            self.__color_occupancy[c] ^= s_bb
            self.__attack_sets[c][_type] = self.test_piece(c, _type).attack_set(self)
        self.squares[s] = None
        return existing_piece_at_s

    def set_enpassant_board(self, c: Color, s: Square) -> None:
        self.__boards[c][PieceType.ENPASSANT] = s.bitboard

    def ep_board(self, c: Color) -> Bitboard:
        return self.__boards[c][PieceType.ENPASSANT]

    def iterpieces(self, c: Color) -> Generator[AbstractPiece, None, None]:
        for piece_type in self.__boards[c]:
            yield self.test_piece(c, piece_type)

    # def __getitem__(self, key):
    #     if isinstance(key, Color):
    #         return getattr(self, f"{key.name.lower()}_occupancy")
    #     elif isinstance(key, AbstractPiece):
    #         return self.board_for(key)
    #     elif isinstance(key, (Square, int)):
    #         return self.squares[key]
    #     else:
    #         raise TypeError("unsupported type for lookup")

    def __hash__(self):
        return hash(tuple(self.squares))



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
        return CastlingRightsEnum(self).name


SubState = NamedTuple("Substate", [
    ("castling", CastlingRights),
    ("captured", AbstractPiece),
    ("ep", Square),
])

class State:
    def __init__(
        self,
        turn: Color = Color.WHITE,
        castling_rights: str = "KQkq",
        ep_square: str = None,
        half_move_clock: int = 0,
        full_move_clock: int = 0,
    ):
        ep_square = Square(Squares[ep_square.upper()]._value_) if ep_square not in ("-", None) else None
        castling_rights = castling_rights if castling_rights != "-" else "none"
        castling_rights = CastlingRights(CastlingRightsEnum[castling_rights]._value_)

        self.half_move_clock = int(half_move_clock)
        self.full_move_clock = int(full_move_clock)
        self.turn = Color.WHITE if turn in ("w", 0) else Color.BLACK
        self.__stack = deque([SubState(castling=castling_rights, captured=None, ep=ep_square)])


    def push(self, captured=None, castling=None, ep_square=None):
        self.full_move_clock += 1
        self.turn = ~self.turn
        cur = self.__stack[0]
        _s = SubState(
            castling=cur.castling ^ (castling << self.turn),
            captured=captured,
            ep=ep_square,
        )
        self.__stack.appendleft(_s)

    def pop(self):
        self.full_move_clock -= 1
        self.turn = ~self.turn
        captured, ep_square = None, None
        if self.__stack:
            return self.__stack.popleft()
        return (CastlingRights(15), None, None)

    @property
    def castling_rights(self):
        return self.__stack[0].castling

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
