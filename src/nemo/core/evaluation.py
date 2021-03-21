from .types import Bitboard, Color, PieceType
from .stacked_bitboard import StackedBitboard
from .utils import popcnt, iter_bitscan_forward, flatten

PIECE_VALUES = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 2.75,
    PieceType.BISHOP: 2.9,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
    PieceType.ENPASSANT: 0,
}

CENTRAL_PREFERENCE_TABLE = flatten(
    [
        [1, 2, 3, 4, 4, 3, 2, 1],
        [2, 3, 4, 5, 5, 4, 3, 2],
        [3, 4, 5, 6, 6, 5, 4, 3],
        [4, 5, 6, 7, 7, 6, 5, 4],
        [4, 5, 6, 7, 7, 6, 5, 4],
        [3, 4, 5, 6, 6, 5, 4, 3],
        [2, 3, 4, 5, 5, 4, 3, 2],
        [1, 2, 3, 4, 4, 3, 2, 1],
    ]
)

PIECE_SQUARE_TABLES = {
    Color.WHITE: {
        PieceType.PAWN: flatten(
            [
                [0] * 8,
                [1] * 8,
                [2] * 8,
                [3] * 8,
                [4] * 8,
                [3] * 8,
                [6] * 8,
                [0] * 8,
            ]
        ),
        PieceType.KING: flatten(
            [
                [1] * 8,
                [1] * 8,
                [1] * 8,
                [1] * 8,
                [1] * 8,
                [2] * 8,
                [5] * 8,
                [10] * 8,
            ]
        ),
        PieceType.KNIGHT: CENTRAL_PREFERENCE_TABLE,
        PieceType.ROOK: CENTRAL_PREFERENCE_TABLE,
        PieceType.BISHOP: CENTRAL_PREFERENCE_TABLE,
        PieceType.QUEEN: CENTRAL_PREFERENCE_TABLE,
    },
    Color.BLACK: {
        PieceType.PAWN: flatten(
            [
                [0] * 8,
                [1] * 8,
                [2] * 8,
                [3] * 8,
                [4] * 8,
                [3] * 8,
                [6] * 8,
                [0] * 8,
            ][::-1]
        ),
        PieceType.KING: flatten(
            [
                [1] * 8,
                [1] * 8,
                [1] * 8,
                [1] * 8,
                [1] * 8,
                [2] * 8,
                [5] * 8,
                [10] * 8,
            ][::-1]
        ),
        PieceType.KNIGHT: CENTRAL_PREFERENCE_TABLE,
        PieceType.ROOK: CENTRAL_PREFERENCE_TABLE,
        PieceType.BISHOP: CENTRAL_PREFERENCE_TABLE,
        PieceType.QUEEN: CENTRAL_PREFERENCE_TABLE,
    }
}

W_MAT = 1.0
W_KS = 0.8
W_ATT = 0.6
W_MOB = 0.05
W_PLAC = 0.01


def material_difference(c: Color, bitboards: StackedBitboard) -> float:
    """Returns the material difference from the perspective of ``c``."""
    score = 0
    for piece_type, self_piece_bb, other_piece_bb in bitboards.iter_material(c):
        score += PIECE_VALUES[piece_type] * popcnt(self_piece_bb) - PIECE_VALUES[
            piece_type
        ] * popcnt(other_piece_bb)
    return score


def attacks(c: Color, bitboards: StackedBitboard) -> float:
    attack = 0
    self_bb = bitboards.by_color(c)
    other_bb = bitboards.by_color(~c)
    for piece_type, self_attack_bb, other_attack_bb in bitboards.iter_attacks(c):
        attack += (
            popcnt(self_attack_bb & other_bb) - (
                popcnt(other_attack_bb & self_bb) - popcnt(self_bb & self_attack_bb)
            )
        )
    return attack

def mobility(c: Color, bitboards: StackedBitboard) -> float:
    mob = 0
    self_bb = bitboards.by_color(c)
    other_bb = bitboards.by_color(~c)
    for piece_type, self_attack_bb, other_attack_bb in bitboards.iter_attacks(c):
        mob += popcnt(self_attack_bb) - popcnt(other_attack_bb)
    return mob

def placement(c: Color, bitboards: StackedBitboard) -> float:
    placement = 0
    self_bb = bitboards.by_color(c)
    other_bb = bitboards.by_color(~c)
    for piece_type, self_piece_bb, other_piece_bb in bitboards.iter_material(c):
        for s in iter_bitscan_forward(self_piece_bb):
            placement += PIECE_SQUARE_TABLES[c][piece_type][s]
        for s in iter_bitscan_forward(other_piece_bb):
            placement -= PIECE_SQUARE_TABLES[~c][piece_type][s]
    return placement


HEURISTICS = [
    (material_difference, W_MAT),
    # (attacks, W_ATT),
    (mobility, W_MOB),
    (placement, W_PLAC)
]


def evaluate(position: "Position") -> float:
    c = position.state.turn
    boards = position.boards
    return sum(
        H(c, boards) * w * cf
        for H, w in HEURISTICS
    )
