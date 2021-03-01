from collections import defaultdict
from functools import lru_cache

from .constants import MAX_SQUARE, MIN_SQUARE, MAX_INT, NORTH, EAST, SOUTH, WEST, NE, SE, SW, NW
from .types import (
    DIRECTIONS,
    EMPTY,
    UNIVERSE,
    Bitboard,
    Color,
    PieceType,
    Square,
    Squares,
    Files,
    Ranks,
)
from .utils import rank_mask, file_mask, diag_mask, antidiag_mask
from typing import Tuple

NOT_A = ~Files.A
NOT_AB = ~Bitboard(Files.A | Files.B)
NOT_H = ~Files.H
NOT_GH = ~Bitboard(Files.G | Files.H)

# One steps
n_one = lambda s: (s << NORTH)
s_one = lambda s: (s >> NORTH)
n_two = lambda s: (s << 16)
s_two = lambda s: (s >> 16)

e_one = lambda s: (s << EAST & NOT_A)
w_one = lambda s: (s >> EAST & NOT_H)

ne_one = lambda s: (s << 9 & NOT_A)
nw_one = lambda s: (s << 7 & NOT_H)
se_one = lambda s: (s >> 7 & NOT_A)
sw_one = lambda s: (s >> 9 & NOT_H)

@lru_cache(maxsize=None)
def relative_second_rank_bb(color: Color) -> Bitboard:
    return Ranks.RANK_2 if color == Color.WHITE else Ranks.RANK_7

@lru_cache(maxsize=None)
def relative_third_rank_bb(color: Color) -> Bitboard:
    return Ranks.RANK_3 if color == Color.WHITE else Ranks.RANK_6

@lru_cache(maxsize=None)
def relative_fourth_rank_bb(color: Color) -> Bitboard:
    return Ranks.RANK_4 if color == Color.WHITE else Ranks.RANK_5

@lru_cache(maxsize=None)
def relative_eigth_rank_bb(color: Color) -> Bitboard:
    return Ranks.RANK_8 if color == Color.WHITE else Ranks.RANK_1

@lru_cache(maxsize=None)
def relative_south(color: Color, bb: Bitboard) -> Bitboard:
    return bb >> 8 if color == Color.WHITE else bb << 8

@lru_cache(maxsize=None)
def square_below(color: Color, s: Square) -> int:
    if not s:
        return None
    return Square(s - 8) if color == Color.WHITE else Square(s + 8)

@lru_cache(maxsize=None)
def square_above(color: Color, s: Square) -> int:
    return Square(s + 8) if color == Color.WHITE else Square(s - 8)

@lru_cache(maxsize=None)
def relative_rook_squares(color: Color, short: bool = True) -> Tuple[Square]:
    """Return the rook squares from, to by color and castling type"""
    if color == Color.WHITE:
        return (Square.H1, Square.F1) if short else (Square.A1, Square.D1)
    elif color == Color.BLACK:
        return (Square.H8, Square.F8) if short else (Square.A8, Square.D8)


@lru_cache(maxsize=None)
def knight_attacks(s: int) -> int:
    return knights_attack_mask(1 << s)

@lru_cache(maxsize=None)
def knights_attack_mask(knights: int) -> int:
    s = knights
    return (
        ((s << 17) & NOT_A)
        | ((s << 15) & NOT_H)
        | ((s << 10) & NOT_AB)
        | ((s << 6) & NOT_GH)
        | ((s >> 17) & NOT_H)
        | ((s >> 15) & NOT_A)
        | ((s >> 10) & NOT_GH)
        | ((s >> 6) & NOT_AB)
    )

@lru_cache(maxsize=None)
def white_pawns_all_attack_mask(pawns: int) -> int:
    return ne_one(pawns) | nw_one(pawns)

@lru_cache(maxsize=None)
def white_pawns_single_attack_mask(pawns: int) -> int:
    return ne_one(pawns) ^ nw_one(pawns)

@lru_cache(maxsize=None)
def white_pawns_double_attack_mask(pawns: int) -> int:
    return ne_one(pawns) & nw_one(pawns)

@lru_cache(maxsize=None)
def black_pawns_all_attack_mask(pawns: int) -> int:
    return se_one(pawns) | sw_one(pawns)

@lru_cache(maxsize=None)
def black_pawns_single_attack_mask(pawns: int) -> int:
    return se_one(pawns) ^ sw_one(pawns)

@lru_cache(maxsize=None)
def black_pawns_double_attack_mask(pawns: int) -> int:
    return se_one(pawns) & sw_one(pawns)

@lru_cache(maxsize=None)
def white_pawns_single_push(pawns: int) -> int:
    return n_one(pawns)

@lru_cache(maxsize=None)
def white_pawns_double_push(pawns: int) -> int:
    return n_two(pawns)

@lru_cache(maxsize=None)
def black_pawns_single_push(pawns: int) -> int:
    return s_one(pawns)

@lru_cache(maxsize=None)
def black_pawns_double_push(pawns: int) -> int:
    return s_two(pawns)

@lru_cache(maxsize=None)
def king_attacks(s: int):
    s = 1 << s
    return n_one(s) | ne_one(s) | e_one(s) | se_one(s) | s_one(s) | sw_one(s) | w_one(s) | nw_one(s)


rank_mask_ex = lambda s: (1 << s) ^ rank_mask(s)
file_mask_ex = lambda s: (1 << s) ^ file_mask(s)
diag_mask_ex = lambda s: (1 << s) ^ diag_mask(s)
antidiag_mask_ex = lambda s: (1 << s) ^ antidiag_mask(s)


ROOK_ATTACKS = [Bitboard(rank_mask_ex(s) | file_mask_ex(s)) for s in range(64)]
BISHOP_ATTACKS = [Bitboard(diag_mask_ex(s) | antidiag_mask_ex(s)) for s in range(64)]
QUEEN_ATTACKS = [Bitboard(BISHOP_ATTACKS[s] | ROOK_ATTACKS[s]) for s in range(64)]
KNIGHT_ATTACKS = [Bitboard(knight_attacks(s)) for s in range(64)]
KING_ATTACKS = [Bitboard(king_attacks(s)) for s in range(64)]
PAWN_ATTACKS = [
    white_pawns_all_attack_mask,
    black_pawns_all_attack_mask,
]
PAWN_SINGLE_PUSHES = [
    white_pawns_single_push,
    black_pawns_single_push,
]
PAWN_DOUBLE_PUSHES = [
    white_pawns_double_push,
    black_pawns_double_push,
]
PAWN_SINGLE_ATTACKS = [
    white_pawns_single_attack_mask,
    black_pawns_single_attack_mask,
]
PAWN_DOUBLE_ATTACKS = [
    white_pawns_single_attack_mask,
    black_pawns_single_attack_mask,
]
