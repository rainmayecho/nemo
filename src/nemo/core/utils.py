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

DEBRUIJN_CONST = Bitboard(0x03F79D71B4CB0A89)


def lsb(v: int) -> int:
    """Returns the least significant bit of the input."""
    return v & -v


def popcnt(v: int) -> int:
    """Returns the number of ones in a binary representation of the input."""
    return bin(v).count("1")


def iter_lsb(bb: int) -> "Generator[int, None, None]":
    bb = int(bb)
    while bb:
        _lsb = lsb(bb)
        yield _lsb
        bb ^= _lsb


def bitscan_forward(bb: int):
    return BITSCAN_INDEX[Bitboard((bb & -bb) * DEBRUIJN_CONST) >> 58]


def iter_bitscan_forward(bb: int) -> "Generator[int, None, None]":
    if bb == 0:
        return

    for isolated_lsb in iter_lsb(bb):
        yield BITSCAN_INDEX[Bitboard(isolated_lsb * DEBRUIJN_CONST) >> 58]
