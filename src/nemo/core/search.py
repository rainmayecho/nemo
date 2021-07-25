import asyncio

from collections import deque
from typing import Iterable, Tuple, NamedTuple

from .constants import INFINITY, QUIESCENCE_SEARCH_DEPTH_PLY
from .evaluation import evaluate
from .move import Move
from .position import Position
from .transposition import TTable, Killers
from .types import Color, SearchResult, Square, NodeType


def quiesce(
    node: Position,
    depth: int = 1,
    alpha: float = -INFINITY,
    beta: float = INFINITY,
    ply: int = 0,
) -> float:
    static_eval = evaluate(node)
    if not depth:
        return static_eval

    if static_eval >= beta:
        return beta
    elif static_eval > alpha:
        alpha = static_eval

    captures = list(node.legal_captures)
    for move in captures:
        node.make_move(move)
        score = -quiesce(node, depth - 1, -beta, -alpha, ply + 1)
        node.unmake_move(move)
        if score >= beta:
            update_killers(move, score, ply)
            return beta
        if score > alpha:
            alpha = score
    return alpha

def probe_ttable(key: int, depth: int = 0) -> SearchResult:
    result = TTable.get(key)
    if result is not None and result.ply > depth:
        return result
    return None

def store_ttable(key: int, result: SearchResult) -> None:
    existing = TTable.get(key)
    if existing is None or (existing is not None and result.ply < existing.ply):
        TTable[key] = result


def update_killers(move: Move, score: float, ply: int) -> None:
    key = hash(move)
    d = Killers[ply]
    if not d.is_full():
        d[key] = (move, score)
    else:
        key_to_pop = min(d.items(), key=lambda e: abs(e[1][1]))[0]
        if abs(d.get(key_to_pop)[1]) < abs(score):
            d.pop(key_to_pop)
            d[key] = (move, score)


def get_ordered_moves(node: Position, ply: int) -> Iterable[Move]:
    def sort_key(move: Move) -> Tuple[int, int, int]:
        return (int(hash(move) in Killers[ply]), move._flags)
    moves = deque(sorted(node.legal_moves, key=lambda m: sort_key(m), reverse=True))
    result = probe_ttable(node.key)
    if result is not None and result.move:
        moves.appendleft(result.move)
    return moves


def negamax(
    node: Position,
    depth: int = 1,
    alpha: float = -INFINITY,
    beta: float = INFINITY,
    ply: int = 0
) -> SearchResult:
    _alpha = alpha

    hash_move = probe_ttable(node.key, depth)
    if hash_move is not None:
        if hash_move.nodetype == NodeType.EXACT:
            return hash_move
        elif hash_move.nodetype == NodeType.ALPHA:
            alpha = max(alpha, hash_move.score)
        elif hash_move.nodetype == NodeType.BETA:
            beta = min(beta, hash_move.score)

        if alpha >= beta:
            return hash_move

    if not depth:
        if len(list(node.legal_captures)):
            return SearchResult(
                depth,
                quiesce(node, QUIESCENCE_SEARCH_DEPTH_PLY, alpha, beta, ply + 1),
                None,
                alpha,
                beta
            )
        return SearchResult(depth, evaluate(node), None, alpha, beta)

    if node.is_checkmate():
        return SearchResult(depth, INFINITY, None, alpha, beta)

    moves = get_ordered_moves(node, ply)
    score = -INFINITY
    best = None
    for move in moves:
        node.make_move(move)
        if node.is_legal:
            score = max(score, -negamax(node, depth - 1, -beta, -alpha, ply + 1).score)
        node.unmake_move(move)
        if score > alpha:
            alpha = score
            best = move
        if alpha >= beta:
            # print(f"{move} caused a cutoff!")
            update_killers(move, score, depth)
            best = move
            break

    result = SearchResult(depth, score, best, alpha, beta)
    if score <= _alpha:
        result.nodetype = NodeType.BETA
    elif score >= beta:
        result.nodetype = NodeType.ALPHA
    else:
        result.nodetype = NodeType.EXACT

    store_ttable(node.key, result)
    return result

def deepen(p: Position, depth: int = 1):
    for d in range(depth):
        result = negamax(p, min(d + 1, 8))
        store_ttable(p.key, result)
    return TTable[p.key]


if __name__ == "__main__":
    p = Position()
    print(negamax(p, 3))
