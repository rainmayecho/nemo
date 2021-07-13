from typing import Tuple, NamedTuple

from .constants import INFINITY
from .position import Position
from .types import Color, SearchResult, Square
from .evaluation import evaluate
from .move import Move

QUIESCENCE_SEARCH_DEPTH_PLY = 3

def quiesce(node: Position, depth: int = 1, alpha: float = -INFINITY, beta: float = INFINITY) -> float:
    static_eval = evaluate(node)
    if not depth:
        return static_eval

    if static_eval >= beta:
        return beta
    elif alpha < static_eval:
        alpha = static_eval

    captures = list(node.legal_captures)
    for move in captures:
        node.make_move(move)
        score = -quiesce(node, depth - 1, -beta, -alpha)
        node.unmake_move(move)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def negamax(
    node: Position,
    depth: int = 1,
    alpha: float = -INFINITY,
    beta: float = INFINITY,
) -> SearchResult:
    if not depth:
        if len(list(node.legal_captures)):
            return SearchResult(
                depth,
                quiesce(node, QUIESCENCE_SEARCH_DEPTH_PLY, alpha, beta),
                None,
                alpha,
                beta
            )
        return SearchResult(depth, evaluate(node), None, alpha, beta)

    if node.is_checkmate():
        return SearchResult(depth, INFINITY, None, alpha, beta)

    moves = sorted(node.legal_moves, key=lambda m: m._flags, reverse=True)
    score = -INFINITY
    best = None
    for move in moves:
        before = node.key
        node.make_move(move)
        _score = -negamax(node, depth - 1, -beta, -alpha).score
        if _score > score:
            score = _score
            best = move
        alpha = max(alpha, score)
        node.unmake_move(move)
        if node.key != before:
            raise
        if alpha >= beta:
            best = move
            break
    return SearchResult(depth, score, best, alpha, beta)


if __name__ == "__main__":
    p = Position()
    print(negamax(p, 3))
