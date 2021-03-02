from sys import argv

from .position import Position
from .constants import STARTING_FEN


def perft(depth: int = 1, fen=STARTING_FEN, position=None):
    position = position or Position(fen=fen)
    n = 0
    moves = list(position.pseudo_legal_moves)
    if not depth:
        return 1
    for move in moves:
        position.make_move(move)
        if position.is_legal():
            n += perft(depth - 1, position=position)
        position.unmake_move(move)

    return n
