from .types import Bitboard, Color, PieceType
from .stacked_bitboard import StackedBitboard
from .utils import popcnt

PIECE_VALUES = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 2.75,
    PieceType.BISHOP: 2.9,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
    PieceType.ENPASSANT: 0,
}

W_MAT = 3.0
W_KS = 1.2
W_CTRL = 9.0


def material_difference(c: Color, bitboards: StackedBitboard) -> float:
    """Returns the material difference from the perspective of ``c``."""
    score = 0
    for piece_type, self_piece_bb, other_piece_bb in bitboards.iter_material(c):
        score += PIECE_VALUES[piece_type] * popcnt(self_piece_bb) - PIECE_VALUES[
            piece_type
        ] * popcnt(other_piece_bb)
    return score * W_MAT


def control(c: Color, bitboards: StackedBitboard) -> float:
    ctrl = 0
    for piece_type, self_attack_bb, other_attack_bb in bitboards.iter_attacks(c):
        ctrl += popcnt(self_attack_bb) - popcnt(other_attack_bb)
    return ctrl * W_CTRL


def evaluate(position: "Position") -> float:
    c = position.state.turn
    boards = position.boards
    return material_difference(c, boards) + control(c, boards)
