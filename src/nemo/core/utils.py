from cProfile import Profile

from .types import Bitboard

BITSCAN_INDEX = [
    0,
    1,
    48,
    2,
    57,
    49,
    28,
    3,
    61,
    58,
    50,
    42,
    38,
    29,
    17,
    4,
    62,
    55,
    59,
    36,
    53,
    51,
    43,
    22,
    45,
    39,
    33,
    30,
    24,
    18,
    12,
    5,
    63,
    47,
    56,
    27,
    60,
    41,
    37,
    16,
    54,
    35,
    52,
    21,
    44,
    32,
    23,
    11,
    46,
    26,
    40,
    15,
    34,
    20,
    31,
    10,
    25,
    14,
    19,
    9,
    13,
    8,
    7,
    6,
]

BIT_TABLE =  [
    63, 30, 3, 32, 25, 41, 22, 33,
    15, 50, 42, 13, 11, 53, 19, 34,
    61, 29, 2, 51, 21, 43, 45, 10,
    18, 47, 1, 54, 9, 57, 0, 35,
    62, 31, 40, 4, 49, 5, 52, 26,
    60, 6, 23, 44, 46, 27, 56, 16,
    7, 39, 48, 24, 59, 14, 12, 55,
    38, 28, 58, 20, 37, 17, 36, 8
]

DEBRUIJN_CONST = Bitboard(0x03F79D71B4CB0A89)


def lsb(v: int) -> int:
    """Returns the least significant bit of the input."""
    return v & -v


def popcnt(v: int) -> int:
    """Returns the number of ones in a binary representation of the input."""
    return bin(v).count("1")


def iter_lsb(bb: int) -> "Generator[int, None, None]":
    # bb = int(bb)
    while bb:
        _lsb = lsb(bb)
        yield _lsb
        bb ^= _lsb

def bitscan_forward(bb: int):
    return BITSCAN_INDEX[Bitboard((bb & -bb) * DEBRUIJN_CONST) >> 58]


def iter_bitscan_forward(bb: int) -> "Generator[int, None, None]":
    for isolated_lsb in iter_lsb(bb):
        yield BITSCAN_INDEX[Bitboard(isolated_lsb * DEBRUIJN_CONST) >> 58]


def rank_mask(s: int) -> int:
    return 0xFF << (s & 56)


def file_mask(s: int) -> int:
    return 0x0101010101010101 << (s & 7)


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


class SectionProfiler:
    def __init__(self, sort_by="cumulative"):
        self.__sort_by = sort_by
        self.profiler = Profile()

    def __enter__(self):
        self.profiler.enable()
        return self

    def __exit__(self, *args):
        self.profiler.print_stats(sort=self.__sort_by)