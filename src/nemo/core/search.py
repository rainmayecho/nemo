import asyncio

from collections import deque, defaultdict
from json import dumps
from typing import Iterable, Tuple, NamedTuple

from .constants import INFINITY, QUIESCENCE_SEARCH_DEPTH_PLY
from .evaluation import evaluate, see
from .move import Move
from .position import Position
from .transposition import TTable, Killers
from .types import Color, SearchResult, Square, NodeType


stats = defaultdict(lambda: defaultdict(int))

class SearchStats:
    def __init__(self):
        self.__stats = defaultdict(lambda: defaultdict(int))

    def update(self, result: SearchResult) -> None:
        if result.move is not None:
            self.__stats[result.ply][result.nodetype] += 1

    def reset(self):
        self.__stats.clear()

    @property
    def info(self):
        return {k: dict(v) for k, v in self.__stats.items()}


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


def get_ordered_moves(node: Position, ply: int, only_captures: bool = False) -> Iterable[Move]:
    def sort_key(move: Move) -> Tuple[int, int, int]:
        see_result = see(node, move) if move.is_capture else 0
        flag = move._flags if move._flags >= 4 else 0
        h = hash(move)
        return (int(h in Killers[ply]), see_result, flag)
    movegen = node.legal_captures if only_captures else node.legal_moves
    moves = deque(sorted(movegen, key=lambda m: sort_key(m), reverse=True))
    result = probe_ttable(node.key)
    if result is not None and result.move:
        moves.appendleft(result.move)
    return moves


class Searcher:
    def __init__(self, event: "threading.Event" = None):
        self.__event = event
        self.__stats = SearchStats()

    @property
    def stopped(self):
        return self.__event is not None and self.__event.is_set()

    @property
    def stats(self):
        return self.__stats.info

    def update_stats(self, result: SearchResult) -> None:
        self.__stats.update(result)

    def reset_stats(self) -> None:
        self.__stats.reset()

    def search(self, p: Position, depth: int = 1):
        self.reset_stats()
        for d in range(depth):
            result = self.negamax(p, d + 1)
            if result:
                store_ttable(p.key, result)
        return TTable[p.key]

    def quiesce(
        self,
        node: Position,
        depth: int = 1,
        alpha: float = -INFINITY,
        beta: float = INFINITY,
        ply: int = 0,
    ) -> float:
        if self.stopped:
            return SearchResult()

        static_eval = evaluate(node)
        if not depth:
            return static_eval

        if static_eval >= beta:
            return beta
        elif static_eval > alpha:
            alpha = static_eval

        captures = get_ordered_moves(node, ply, only_captures=True)
        for move in captures:
            node.make_move(move)
            score = -self.quiesce(node, depth - 1, -beta, -alpha, ply + 1)
            node.unmake_move(move)
            if score >= beta:
                update_killers(move, score, ply)
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def negamax(
        self,
        node: Position,
        depth: int = 1,
        alpha: float = -INFINITY,
        beta: float = INFINITY,
        ply: int = 0,
    ) -> SearchResult:
        if self.stopped:
            return SearchResult()

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
                    self.quiesce(node, QUIESCENCE_SEARCH_DEPTH_PLY, alpha, beta, ply + 1),
                    None,
                    alpha,
                    beta
                )
            return SearchResult(depth, evaluate(node), None, alpha, beta)

        if node.is_checkmate():
            return SearchResult(depth, -INFINITY, None, alpha, beta)

        moves = get_ordered_moves(node, ply)
        score = -INFINITY
        best = None
        for move in moves:
            node.make_move(move)
            if node.is_legal:
                score = max(score, -self.negamax(node, depth - 1, -beta, -alpha, ply + 1).score)
                # print(f"considering {move}...{score}")
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
        self.update_stats(result)
        store_ttable(node.key, result)
        return result


if __name__ == "__main__":
    p = Position()
    print(Searcher(p, 3).search())
