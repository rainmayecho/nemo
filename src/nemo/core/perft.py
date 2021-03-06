from json import dumps
from sys import argv

from .position import Position
from .constants import STARTING_FEN
from .move import MoveFlags
from .utils import lsb


class NodeStat:
    ATTRS = ("nodes", "captures", "ep", "castles", "promotions")

    def __init__(self, n=0):
        self.nodes = n
        self.captures = 0
        self.ep = 0
        self.castles = 0
        self.promotions = 0

    def update_from_move(self, move: "Move") -> None:
        if move.flags in (MoveFlags.KINGSIDE_CASTLE, MoveFlags.QUEENSIDE_CASTLE):
            self.castles += 1
        elif move.is_capture:
            self.captures += 1
        elif move.is_enpassant_capture:
            self.ep += 1
        elif move.is_promotion:
            self.promotions += 1

    def __add__(self, other: "NodeStat"):
        for k in self.ATTRS:
            x, y = getattr(self, k), getattr(other, k)
            setattr(self, k, x + y)
        return self

    def __str__(self) -> str:
        return dumps({k: getattr(self, k, 0) for k in self.ATTRS}, separators=(",", ": "), indent=4)


def perft(depth: int = 1, fen=STARTING_FEN, position=None) -> NodeStat:
    position = position or Position(fen=fen)
    n = NodeStat()
    moves = list(position.pseudo_legal_moves)
    if not depth:
        return NodeStat(1)
    for move in moves:
        position.make_move(move)
        if position.is_legal():
            n += perft(depth - 1, position=position)
            n.update_from_move(move)
        position.unmake_move(move)

    return n
