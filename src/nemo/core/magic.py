from functools import reduce
from operator import ior
from pickle import dump, load, HIGHEST_PROTOCOL
from random import getrandbits
from typing import Tuple, Dict, List

from .utils import (
    popcnt,
    lsb,
    rank_mask,
    file_mask,
    diag_mask,
    antidiag_mask,
    BIT_TABLE,
)
from .types import Bitboard, Square, Ranks, Files, Squares, EMPTY

NOT_EDGES = ~(Ranks.RANK_8 | Ranks.RANK_1 | Files.A | Files.H)
MAX_INT_32 = 2 ** 32 - 1


PIN_MASKS = {}
RAY_MASKS = {}


def rook_mask(s: Square) -> Bitboard:
    """Generates the relevant blocker mask for a rook on square s."""
    r, f = divmod(s, 8)
    mask = Bitboard(0)
    for _r in range(1, 7):
        mask |= (1 << (_r * 8 + f)) if _r != r else 0
    for _f in range(1, 7):
        mask |= (1 << (r * 8 + _f)) if _f != f else 0
    return mask


def bishop_mask(s: Square) -> Bitboard:
    """Generates the relevant blocker mask for a bishop on square s."""
    mask = Bitboard(diag_mask(s) | antidiag_mask(s)) ^ (1 << s)
    return mask & NOT_EDGES


def rook_attacks(s: int, blockers: Bitboard) -> Bitboard:
    attacks = Bitboard(0)
    r, f = divmod(s, 8)

    for _r in range(r + 1, 8):
        sb = 1 << (_r * 8 + f)
        attacks |= sb
        if blockers & sb:
            break

    for _r in range(r - 1, -1, -1):
        sb = 1 << (_r * 8 + f)
        attacks |= sb
        if blockers & sb:
            break

    for _f in range(f + 1, 8):
        sb = 1 << (r * 8 + _f)
        attacks |= sb
        if blockers & sb:
            break

    for _f in range(f - 1, -1, -1):
        sb = 1 << (r * 8 + _f)
        attacks |= sb
        if blockers & sb:
            break

    return attacks


def bishop_attacks(s: int, blockers: Bitboard) -> Bitboard:
    attacks = Bitboard(0)
    r, f = divmod(s, 8)

    _r, _f = r + 1, f + 1
    while _r < 8 and _f < 8:
        sb = 1 << (_r * 8 + _f)
        attacks |= sb
        if blockers & sb:
            break
        _r += 1
        _f += 1

    _r, _f = r + 1, f - 1
    while _r < 8 and _f >= 0:
        sb = 1 << (_r * 8 + _f)
        attacks |= sb
        if blockers & sb:
            break
        _r += 1
        _f -= 1

    _r, _f = r - 1, f + 1
    while _r >= 0 and _f < 8:
        sb = 1 << (_r * 8 + _f)
        attacks |= sb
        if blockers & sb:
            break
        _r -= 1
        _f += 1

    _r, _f = r - 1, f - 1
    while _r >= 0 and _f >= 0:
        sb = 1 << (_r * 8 + _f)
        attacks |= sb
        if blockers & sb:
            break
        _r -= 1
        _f -= 1

    return attacks


# Rook blocker occupancy bitmasks
ROOK_MASK = [rook_mask(s) for s in range(64)]
BISHOP_MASK = [bishop_mask(s) for s in range(64)]

# Lookup of number of blocker bits by square index
ROOK_BITS = [popcnt(m) for m in ROOK_MASK]
BISHOP_BITS = [popcnt(m) for m in BISHOP_MASK]


def bishop_mapping(s: int) -> Dict[int, List[int]]:
    d = {}
    n = BISHOP_BITS[s]
    mask = BISHOP_MASK[s]
    for i in range(1 << n):
        b = index_to_bitboard(i, n, mask)
        d[b] = bishop_attacks(s, b)
    return d


def rook_mapping(s: int) -> Dict[int, List[int]]:
    d = {}
    n = ROOK_BITS[s]
    mask = ROOK_MASK[s]
    for i in range(1 << n):
        b = index_to_bitboard(i, n, mask)
        d[b] = rook_attacks(s, b)
    return d


def _pop_lsb(v: int) -> Tuple[int, int]:
    b = v ^ (v - 1)
    fold = (b & 0xFFFFFFFF) ^ (b >> 32)
    v &= v - 1
    return v, BIT_TABLE[((fold * 0x783A9B23) & 0xFFFFFFFF) >> 26]


def index_to_bitboard(idx: int, bits: int, mask: Bitboard) -> Bitboard:
    result = Bitboard(0)
    v = int(mask)
    for i in range(bits):
        v, j = _pop_lsb(v)
        if idx & (1 << i):
            result |= 1 << j
    return result


def random_magic():
    def _rand():
        return reduce(ior, ((getrandbits(64) & 0xFFFF) << (i * 16) for i in range(4)))

    return _rand() & _rand() & _rand()


def transform(b: int, magic: int, bits: int) -> int:
    return Bitboard(b * magic) >> (64 - bits)


def generate_magic(s: int, bits: int, bishop: bool):
    """Generate magic bitboards for fast lookups on sliding piece attacks.

    Taken from: https://www.chessprogramming.org/Looking_for_Magics

    We are precomputing the attack set considering
    all variations of blockers (max 4096 == 2**12, rook on a1)

    """
    a, b, used = [0] * 4096, [0] * 4096, [0] * 4096
    mask = bishop_mask(s) if bishop else rook_mask(s)
    n = popcnt(mask)
    print(
        f"Generating Attack Set for {'bishop' if bishop else 'rook'} on {Squares(s).name}..."
    )
    for i in range(1 << n):
        b[i] = index_to_bitboard(i, n, mask)
        a[i] = bishop_attacks(s, b[i]) if bishop else rook_attacks(s, b[i])

    for k in range(10000000):
        magic = random_magic()
        if popcnt((magic * mask) & 0xFF00000000000000) < 6:
            continue
        i, failed = 0, 0
        upperbound = 1 << n
        used = [0] * 4096
        while i < upperbound:
            j = transform(b[i], magic, bits)
            if not used[j]:
                used[j] = a[i]
            elif used[j] != a[i]:
                failed = 1
                break
            i += 1
        if not failed:
            return magic, used


def regenerate_magic():
    global ROOK_MAGIC
    global BISHOP_MAGIC
    global ROOK_ATTACKS
    global BISHOP_ATTACKS

    ROOK_MAGIC = [0] * 64
    BISHOP_MAGIC = [0] * 64
    ROOK_ATTACKS = [0] * 64
    BISHOP_ATTACKS = [0] * 64

    for s in range(64):
        magic, attacks = generate_magic(s, ROOK_BITS[s], 0)
        ROOK_MAGIC[s] = magic
        ROOK_ATTACKS[s] = attacks

    for s in range(64):
        magic, attacks = generate_magic(s, BISHOP_BITS[s], 1)
        BISHOP_MAGIC[s] = magic
        BISHOP_ATTACKS[s] = attacks

    nl = "\n"
    tab = "\t"
    print(
        f"BISHOP_MAGIC = [{nl}{tab}{f',{nl}{tab}'.join(f'Bitboard({hex(bb)})' for bb in  BISHOP_MAGIC)}{nl}]"
    )
    print(
        f"ROOK_MAGIC = [{nl}{tab}{f',{nl}{tab}'.join(f'Bitboard({hex(bb)})' for bb in ROOK_MAGIC)}{nl}]"
    )
    with open("magic.pickle", "wb") as fp:
        dump(
            (BISHOP_ATTACKS, ROOK_ATTACKS, BISHOP_MAGIC, ROOK_MAGIC),
            fp,
            protocol=HIGHEST_PROTOCOL,
        )


try:
    with open("magic.pickle", "rb") as fp:
        BISHOP_ATTACKS, ROOK_ATTACKS, BISHOP_MAGIC, ROOK_MAGIC = load(fp)
except Exception:
    regenerate_magic()


# pin lookup
def generate_pin_masks():
    global PIN_MASKS
    for i in range(64):
        for j in range(i + 1, 64):
            __rank = rank_mask(i) & rank_mask(j)
            __file = file_mask(i) & file_mask(j)
            __diag = diag_mask(i) & diag_mask(j)
            __antidiag = antidiag_mask(i) & antidiag_mask(j)

            __mask = Bitboard(__rank | __file | __diag | __antidiag)
            if __mask:
                PIN_MASKS[(i, j)] = __mask
                PIN_MASKS[(j, i)] = __mask


def generate_rays():
    global RAY_MASKS
    for i in range(64):
        for j in range(i + 1, 64):
            __mask = Bitboard(0)
            if j // 8 == i // 8:  # +1 dir
                d = 1
            elif diag_mask(i) & diag_mask(j):  # +9 dir
                d = 9
            elif antidiag_mask(i) & antidiag_mask(j):  # +7 dir
                d = 7
            elif i % 8 == j % 8:  # +8 dir
                d = 8
            else:
                RAY_MASKS[(i, j)] = __mask
                RAY_MASKS[(j, i)] = __mask
                continue

            k = i + d
            while k < j:
                __mask |= 1 << k
                k += d

            RAY_MASKS[(i, j)] = __mask
            RAY_MASKS[(j, i)] = __mask


generate_pin_masks()
generate_rays()


class Magic:
    @staticmethod
    def bishop_attacks(s: int, occ: Bitboard) -> Bitboard:
        occ &= BISHOP_MASK[s]
        occ *= BISHOP_MAGIC[s]
        idx = Bitboard(occ) >> (64 - BISHOP_BITS[s])
        return BISHOP_ATTACKS[s][idx]

    @staticmethod
    def rook_attacks(s: int, occ: Bitboard) -> Bitboard:
        occ &= ROOK_MASK[s]
        occ *= ROOK_MAGIC[s]
        idx = Bitboard(occ) >> (64 - ROOK_BITS[s])
        return ROOK_ATTACKS[s][idx]

    @staticmethod
    def get_pin_mask(s1: Square, s2: Square) -> Bitboard:
        return PIN_MASKS.get((s1, s2), EMPTY)

    @staticmethod
    def get_ray_mask(s1: Square, s2: Square) -> Bitboard:
        return RAY_MASKS.get((s1, s2), EMPTY)
