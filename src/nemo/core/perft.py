from .position import Position


def perft(depth: int = 1, fen: str = None):
    n = 0
    legal_moves = position.legal_moves
    if n == 1:
        return len(legal_moves)

    for move in legal_moves:
        # position.make_move(move)
        n += perft(depth - 1)
        # position.unmake(move)

    return n
