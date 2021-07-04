from .types import Bitboard, Color, PieceType
from .stacked_bitboard import StackedBitboard
from .utils import popcnt, iter_bitscan_forward, flatten

PIECE_VALUES = {
    PieceType.ENPASSANT: 0,
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 20000,
}

W_PAWNS_TABLE = flatten(
    [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 10, 25, 25, 10,  5,  5],
        [0,  0,  0, 20, 20,  0,  0,  0],
        [5, -5,-10,  0,  0,-10, -5,  5],
        [5, 10, 10,-20,-20, 10, 10,  5],
        [0,  0,  0,  0,  0,  0,  0,  0],
    ][::-1]
)

B_PAWNS_TABLE = flatten(
    [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 10, 25, 25, 10,  5,  5],
        [0,  0,  0, 20, 20,  0,  0,  0],
        [5, -5,-10,  0,  0,-10, -5,  5],
        [5, 10, 10,-20,-20, 10, 10,  5],
        [0,  0,  0,  0,  0,  0,  0,  0],
    ]
)

KNIGHTS_TABLE = flatten(
    [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20,   0,   0,   0,   0, -20, -40],
        [-30,   0,  10,  15,  15,  10,   0, -30],
        [-30,   5,  15,  20,  20,  15,   5, -30],
        [-30,   0,  15,  20,  20,  15,   0, -30],
        [-30,   5,  10,  15,  15,  10,   5, -30],
        [-40, -20,   0,   5,   5,   0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ]
)

W_BISHOPS_TABLE = flatten(
    [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ][::-1]
)

B_BISHOPS_TABLE = flatten(
    [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ]
)

W_ROOKS_TABLE = flatten(
    [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [0,  0,  0,  5,  5,  0,  0,  0],
    ][::-1]
)

B_ROOKS_TABLE = flatten(
    [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [0,  0,  0,  5,  5,  0,  0,  0],
    ]
)

W_QUEENS_TABLE = flatten(
    [
        [-20,-10,-10 , -5, -5,-10,-10,-20],
        [-10 ,  0,  0,  0,  0,  0,  0,-10],
        [-10 ,  0,  5,  5,  5,  5,  0,-10],
        [-5 ,  0,  5,  5,  5,  5,  0, -5],
        [0,  0,  5,  5,  5,  5,  0, -5],
        [-10 ,  5,  5,  5,  5,  5,  0,-10],
        [-10 ,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10 , -5, -5,-10,-10,-20],
    ][::-1]
)

B_QUEENS_TABLE = flatten(
    [
        [-20,-10,-10 , -5, -5,-10,-10,-20],
        [-10 ,  0,  0,  0,  0,  0,  0,-10],
        [-10 ,  0,  5,  5,  5,  5,  0,-10],
        [-5 ,  0,  5,  5,  5,  5,  0, -5],
        [0,  0,  5,  5,  5,  5,  0, -5],
        [-10 ,  5,  5,  5,  5,  5,  0,-10],
        [-10 ,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10 , -5, -5,-10,-10,-20],
    ]
)

W_KINGS_TABLE = flatten(
    [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [20, 20,  0,  0,  0,  0, 20, 20],
        [20, 30, 10,  0,  0, 10, 30, 20],
    ][::-1]
)

B_KINGS_TABLE = flatten(
    [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [20, 20,  0,  0,  0,  0, 20, 20],
        [20, 30, 10,  0,  0, 10, 30, 20],
    ]
)


PIECE_SQUARE_TABLES = {
    Color.WHITE: {
        PieceType.PAWN: W_PAWNS_TABLE,
        PieceType.KING: W_KINGS_TABLE,
        PieceType.KNIGHT: KNIGHTS_TABLE,
        PieceType.ROOK: W_ROOKS_TABLE,
        PieceType.BISHOP: W_BISHOPS_TABLE,
        PieceType.QUEEN: W_QUEENS_TABLE,
    },
    Color.BLACK: {
        PieceType.PAWN: B_PAWNS_TABLE,
        PieceType.KING: B_KINGS_TABLE,
        PieceType.KNIGHT: KNIGHTS_TABLE,
        PieceType.ROOK: B_ROOKS_TABLE,
        PieceType.BISHOP: B_BISHOPS_TABLE,
        PieceType.QUEEN: B_QUEENS_TABLE,
    },
}

W_MAT = 1.0
W_KS = 0.8
W_ATT = .2
W_MOB = .2
W_PLAC = 1.0


def material_difference(c: Color, bitboards: StackedBitboard) -> float:
    """Returns the material difference from the perspective of ``c``."""
    score = 0
    for piece_type, self_piece_bb, other_piece_bb in bitboards.iter_material(c):
        score += (PIECE_VALUES[piece_type] * popcnt(self_piece_bb)) - (PIECE_VALUES[
            piece_type
        ] * popcnt(other_piece_bb))
    return score


def attacks(c: Color, bitboards: StackedBitboard) -> float:
    attack = 0
    self_bb = bitboards.by_color(c)
    other_bb = bitboards.by_color(~c)
    for piece_type, self_attack_bb, other_attack_bb in bitboards.iter_attacks(c):
        attack += popcnt(self_attack_bb & other_bb) - (
            popcnt(other_attack_bb & self_bb) - popcnt(self_bb & self_attack_bb)
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
    (attacks, W_ATT),
    (mobility, W_MOB),
    (placement, W_PLAC),
]


def evaluate(position: "Position") -> float:
    c = position.state.turn
    boards = position.boards
    return sum(H(c, boards) * w for H, w in HEURISTICS)
