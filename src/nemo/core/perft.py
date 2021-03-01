from .position import Position
from .constants import STARTING_FEN

skip = False

def perft(depth: int = 1, position=None, fen=STARTING_FEN):
    global skip
    position = position or Position(fen=fen)
    n = 0
    moves = list(position.pseudo_legal_moves)
    if not depth:
        return 1
    for move in moves:
        position.make_move(move)
        if position.is_legal():
            if not skip:
                print(position)
                skip = bool(input())
            n += perft(depth - 1, position)
        position.unmake_move(move)

    return n
