from random import getrandbits, seed
from typing import List

from .types import Color, ATTACKERS

seed(131071)
ZOBRIST_KEYS = [[0] * 64 for _ in range(13)]
ZOBRIST_CASTLE = [0] * 16  # 16 distinct castling rights
ZOBRIST_EP = [0] * 8  # 8 distinct en-passant locations (per color)
ZOBRIST_TURN = 0


def init_zobrist():
    global ZOBRIST_KEYS
    global ZOBRIST_CASTLE
    global ZOBRIST_EP
    global ZOBRIST_TURN

    for c in Color:
        for a in ATTACKERS:
            k = (a + (6 * c)) - 1
            for j in range(64):
                ZOBRIST_KEYS[k][j] = getrandbits(64)
    ZOBRIST_CASTLE = [getrandbits(64) for _ in range(16)]
    ZOBRIST_EP = [getrandbits(64) for _ in range(8)]
    ZOBRIST_TURN = getrandbits(64)


init_zobrist()
