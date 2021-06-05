from typing import Tuple

from .position import Position
from .types import Color
from .evaluation import evaluate
from .move import Move


INFINITY = float("inf")


def negamax(
    node: Position,
    depth: int = 1,
    alpha: float = -INFINITY,
    beta: float = INFINITY,
) -> Tuple[float, Move]:
    if not depth:
        return evaluate(node), None

    moves = node.legal_moves
    score = -INFINITY
    best = None
    for move in moves:
        node.make_move(move)
        _score = -negamax(node, depth - 1, -beta, -alpha)[0]
        if _score > score:
            score = _score
            best = move
        alpha = max(alpha, score)
        node.unmake_move(move)
        if alpha >= beta:
            best = move
            break
    return (score, best)


if __name__ == "__main__":
    p = Position()
    print(negamax(p, 3))
