from typing import Tuple

from .types import Bitboard, Color, PieceType, Square, AbstractPiece, EMPTY
from .move import Move
from .stacked_bitboard import StackedBitboard
from .utils import popcnt, iter_bitscan_forward, flatten

PIECE_VALUES = {
    PieceType.NULL: 0,
    PieceType.ENPASSANT: 0,
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 280,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 490,
    PieceType.QUEEN: 900,
    PieceType.KING: 20000,
}

MATE_UPPER = (
    PIECE_VALUES[PieceType.QUEEN] * 8 +
    2 * (
        PIECE_VALUES[PieceType.KNIGHT] +
        PIECE_VALUES[PieceType.BISHOP] +
        PIECE_VALUES[PieceType.ROOK]
    )
)
MATE_LOWER = (
    PIECE_VALUES[PieceType.QUEEN] * 8 -
    2 * (
        PIECE_VALUES[PieceType.KNIGHT] +
        PIECE_VALUES[PieceType.BISHOP] +
        PIECE_VALUES[PieceType.ROOK]
    )
)

W_PAWNS_TABLE = flatten(
    [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 15, 27, 27, 15,  5,  5],
        [0,  0,  0, 25, 25,  0,  0,  0],
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
        [0,  0,  0, 25, 25,  0,  0,  0],
        [5,  5, 15, 27, 27, 15,  5,  5],
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
        [15, 20, 20, 20, 20, 20, 20, 15],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  5,  5,  0,  0,  0],
    ][::-1]
)

B_ROOKS_TABLE = flatten(
    [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [15, 20, 20, 20, 20, 20, 20, 15],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
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
        [25, 40, 10,  0,  0, 10, 40, 25],
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
        [25, 40, 10,  0,  0, 10, 40, 25],
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
W_PLAC = 1.25


def least_valuable_attacker(c: Color, bitboards: StackedBitboard, attack_defend_bb: Bitboard) -> Tuple[Bitboard, AbstractPiece]:
    for piece_type in list(PieceType)[1:-1]:
        piece = bitboards.test_piece(c, piece_type)
        intersect = bitboards.board_for(piece) & attack_defend_bb
        if intersect:
            return (lsb(intersect), piece)
        piece = bitboards.test_piece(~c, piece_type)
        intersect = bitboards.board_for(piece) & attack_defend_bb
        if intersect:
            return (lsb(intersect), piece._type)
    return (EMPTY, PieceType.NULL)


def static_exchange_evaluation(c: Color, bitboards: StackedBitboard, move: Move = None) -> float:
    if move is None:
        return 0
    i = 0
    gain = [0] * 32
    target = boards.piece_at(move._to)
    occ = boards.occupancy
    from_bb = move._from.bitboard
    attack_defend_bb = bitboards.attack_defend_to(_to, c)
    xrays = boards.xrays_bb
    gain[i] = PIECE_VALUES[target._type]
    assert target is not None

    pt = PieceType.NULL
    while True:
        i += 1
        gain[i] = PIECE_VALUES[pt] - gain[i-1]
        if max(-gain[i-1], gain[i]) < 0:
            break

        attack_defend_bb ^= from_bb
        occ ^= from_bb
        from_bb, pt = least_valuable_attacker(i & 1, bitboards, attack_defend_bb)
        if not from_bb:
            break

    i -= 1
    while i:
        gain[i-1] = -max(-gain[i-1], gain[i])
    return gain[0]


def material_difference(c: Color, bitboards: StackedBitboard, **kwargs) -> float:
    """Returns the material difference from the perspective of ``c``."""
    score = 0
    for piece_type, self_piece_bb, other_piece_bb in bitboards.iter_material(c):
        score += (PIECE_VALUES[piece_type] * popcnt(self_piece_bb)) - (PIECE_VALUES[
            piece_type
        ] * popcnt(other_piece_bb))
    return score


def attacks(c: Color, bitboards: StackedBitboard, **kwargs) -> float:
    attack = 0
    self_bb = bitboards.by_color(c)
    other_bb = bitboards.by_color(~c)
    for piece_type, self_attack_bb, other_attack_bb in bitboards.iter_attacks(c):
        attack += popcnt(self_attack_bb & other_bb) - (
            popcnt(other_attack_bb & self_bb) - popcnt(self_bb & self_attack_bb)
        )
    return attack


def mobility(c: Color, bitboards: StackedBitboard, **kwargs) -> float:
    mob = 0
    self_bb = bitboards.by_color(c)
    other_bb = bitboards.by_color(~c)
    for piece_type, self_attack_bb, other_attack_bb in bitboards.iter_attacks(c):
        mob += popcnt(self_attack_bb) - popcnt(other_attack_bb)
    return mob


def placement(c: Color, bitboards: StackedBitboard, **kwargs) -> float:
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
    # (mobility, W_MOB),
    (placement, W_PLAC),
]


def evaluate(position: "Position") -> float:
    c = position.state.turn
    boards = position.boards
    return sum(H(c, boards) * w for H, w in HEURISTICS)
