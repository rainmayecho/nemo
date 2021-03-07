from json import dumps

from .constants import STARTING_FEN
from .move import MoveFlags
from .position import Position



class NodeStat:
    ATTRS = ("nodes", "captures", "ep", "castles", "promotions", "checks")

    def __init__(self, n=0):
        self.nodes = n
        self.captures = 0
        self.ep = 0
        self.castles = 0
        self.promotions = 0
        self.checks = 0

    def update_from_move(self, move: "Move", position: Position) -> None:
        self.castles += bool(move.flags in (MoveFlags.KINGSIDE_CASTLE, MoveFlags.QUEENSIDE_CASTLE))
        self.captures += bool(move.is_capture)
        self.ep += bool(move.is_enpassant_capture)
        self.promotions += bool(move.is_promotion)
        self.checks += bool(position.is_check())
        return self

    def __add__(self, other: "NodeStat"):
        for k in self.ATTRS:
            x, y = getattr(self, k), getattr(other, k)
            setattr(self, k, x + y)
        return self

    def __str__(self) -> str:
        return dumps({k: getattr(self, k, 0) for k in self.ATTRS}, separators=(",", ": "), indent=4)


def perft(depth: int = 1, fen=STARTING_FEN, position=None, move=None) -> NodeStat:
    position = position or Position(fen=fen)
    moves = list(position.pseudo_legal_moves)
    n = NodeStat()
    if not depth:
        return NodeStat(1).update_from_move(move, position)
    for move in moves:
        position.make_move(move)
        if position.is_legal():
            n += perft(depth - 1, position=position, move=move)
        position.unmake_move(move)
    return n
