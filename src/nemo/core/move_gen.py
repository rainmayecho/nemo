from collections import defaultdict
from .constants import MAX_SQUARE, MIN_SQUARE, MAX_INT, NORTH, EAST, SOUTH, WEST, NE, SE, SW, NW
from .types import DIRECTIONS, EMPTY, UNIVERSE, BitBoard, PieceType, Square, Squares, Files, Ranks

rank_mask = lambda s: (0xFF) << (s & 56)
file_mask = lambda s: (0x0101010101010101) << (s & 7)


def diag_mask(s: int) -> int:
    md = 0x8040201008040201
    d = ((s & 7) << 3) - (s & 56)
    n = -d & (d >> 31)
    s = d & (-d >> 31)
    return (md >> s) << n


def antidiag_mask(s: int) -> int:
    md = 0x0102040810204080
    d = 56 - ((s & 7) << 3) - (s & 56)
    n = -d & (d >> 31)
    s = d & (-d >> 31)
    return (md >> s) << n


rank_mask_ex = lambda s: (1 << s) ^ rank_mask(s)
file_mask_ex = lambda s: (1 << s) ^ file_mask(s)
diag_mask_ex = lambda s: (1 << s) ^ diag_mask(s)
antidiag_mask_ex = lambda s: (1 << s) ^ antidiag_mask(s)


ROOK_ATTACKS = [BitBoard(rank_mask_ex(s) | file_mask_ex(s)) for s in range(64)]
BISHOP_ATTACKS = [BitBoard(diag_mask_ex(s) | antidiag_mask_ex(s)) for s in range(64)]
QUEEN_ATTACKS = [BitBoard(BISHOP_ATTACKS[s] | ROOK_ATTACKS[s]) for s in range(64)]
