from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List

from .constants import NE, NORTH, NW, SE, SOUTH, SW
from .move import Move, MoveFlags
from .move_gen import (
    KING_ATTACKS,
    KNIGHT_ATTACKS,
    PAWN_ATTACKS,
    PAWN_DOUBLE_ATTACKS,
    PAWN_DOUBLE_PUSHES,
    PAWN_SINGLE_ATTACKS,
    PAWN_SINGLE_PUSHES,
    QUEEN_ATTACKS,
    ROOK_ATTACKS,
    relative_eigth_rank_bb,
    relative_second_rank_bb,
)
from .types import PIECE_REGISTRY, PIECE_SYMBOL_MAP, RANKS, Bitboard, Color, Piece, PieceType, StackedBitboard
from .utils import iter_bitscan_forward, iter_lsb


class Pawn(Piece):
    _type = PieceType.PAWN

    @lru_cache(maxsize=4096)
    def captures(self, bitboards: StackedBitboard) -> List[Move]:
        c = self.color
        pawns = bitboards[self]
        other_occupancy = bitboards[~c]
        captures = []
        for pawn_bb in iter_lsb(pawns):
            _from = next(iter_bitscan_forward(pawn_bb))
            attack_set = PAWN_ATTACKS[c](pawn_bb) & other_occupancy
            promotion_attack_set = attack_set & relative_eigth_rank_bb(c)
            enpassant_attack_set = attack_set & bitboards.board_for(PIECE_REGISTRY["ep"](~c))
            attack_set = attack_set & ~promotion_attack_set
            attack_set = attack_set & ~enpassant_attack_set

            for _to in iter_bitscan_forward(promotion_attack_set):
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_Q_CAPTURE))
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_N_CAPTURE))
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_R_CAPTURE))
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_B_CAPTURE))

            for _to in iter_bitscan_forward(enpassant_attack_set):
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.ENPASSANT_CAPTURE))

            for _to in iter_bitscan_forward(attack_set):
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES))

        return captures

    @lru_cache(maxsize=4096)
    def quiet_moves(
        self, bitboards: StackedBitboard
    ) -> List[Move]:
        c = self.color
        pawns, occupancy, other_occupancy = (
            bitboards[self], bitboards[c], bitboards[~c]
        )

        occupied_bb = (occupancy | other_occupancy) ^ pawns
        unmoved_pawns = pawns & relative_second_rank_bb(c)

        double_pawn_pushes = PAWN_DOUBLE_PUSHES[c](unmoved_pawns) & ~occupied_bb
        single_pawn_pushes = PAWN_SINGLE_PUSHES[c](pawns) & ~occupied_bb
        promotions = single_pawn_pushes & relative_eigth_rank_bb(c)
        single_pawn_pushes = single_pawn_pushes & ~promotions

        SINGLE_PUSH_DIR = NORTH if c == Color.WHITE else SOUTH
        DOUBLE_PUSH_DIR = SINGLE_PUSH_DIR * 2

        moves = []
        for _to in iter_bitscan_forward(promotions):
            _from = _to - SINGLE_PUSH_DIR
            moves.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_Q))
            moves.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_N))
            moves.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_R))
            moves.append(Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_B))

        for _to in iter_bitscan_forward(double_pawn_pushes):
            moves.append(
                Move(_from=_to - DOUBLE_PUSH_DIR, _to=_to, flags=MoveFlags.DOUBLE_PAWN_PUSH)
            )

        for _to in iter_bitscan_forward(single_pawn_pushes):
            moves.append(Move(_from=_to - SINGLE_PUSH_DIR, _to=_to, flags=MoveFlags.QUIET))

        return moves


class Knight(Piece):
    _type = PieceType.KNIGHT

    @lru_cache(maxsize=4096)
    def captures(self, bitboards: StackedBitboard) -> List[Move]:
        c = self.color
        knights = bitboards[self]
        other_occupancy = bitboards[~c]
        captures = []
        for knight_bb in lsb(knights):
            _from = next(iter_bitscan_forward(knight_bb))
            attack_set = KNIGHT_ATTACKS[_from] & other_occupancy
            for _to in iter_bitscan_forward(attack_set):
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES))

    @lru_cache(maxsize=4096)
    def quiet_moves(self, bitboards: StackedBitboard) -> List[Move]:
        c = self.color
        knights = bitboards[self]
        other_occupancy = bitboards[~c]
        unoccupied = ~(bitboards[c] | other_occupancy)
        moves = []
        for knight_bb in lsb(knights):
            _from = next(iter_bitscan_forward(knight_bb))
            jump_set = KNIGHT_ATTACKS[_from] & unoccupied
            for _to in iter_bitscan_forward(jump_set):
                moves.append(Move(_from=_from, _to=_to, flags=MoveFlags.QUIET))
        return moves


class Bishop(Piece):
    _type = PieceType.BISHOP

    @lru_cache(maxsize=4096)
    def captures(self, bitboards: StackedBitboard) -> List[Move]:
        return []

    @lru_cache(maxsize=4096)
    def quiet_moves(self, bitboards: StackedBitboard) -> List[Move]:
        return []


class Rook(Piece):
    _type = PieceType.ROOK

    @lru_cache(maxsize=4096)
    def captures(self, bitboards: StackedBitboard) -> List[Move]:
        return []

    @lru_cache(maxsize=4096)
    def quiet_moves(self, bitboards: StackedBitboard) -> List[Move]:
        return []


class Queen(Piece):
    _type = PieceType.QUEEN

    @lru_cache(maxsize=4096)
    def captures(self, bitboards: StackedBitboard) -> List[Move]:
        return []

    @lru_cache(maxsize=4096)
    def quiet_moves(self, bitboards: StackedBitboard) -> List[Move]:
        return []


class King(Piece):
    _type = PieceType.KING

    @lru_cache(maxsize=4096)
    def captures(self, bitboards: StackedBitboard) -> List[Move]:
        c = self.color
        knights = bitboards[self]
        other_occupancy = bitboards[~c]
        captures = []
        for knight_bb in lsb(knights):
            _from = next(iter_bitscan_forward(knight_bb))
            attack_set = KING_ATTACKS[_from] & other_occupancy
            for _to in iter_bitscan_forward(attack_set):
                captures.append(Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES))

    @lru_cache(maxsize=4096)
    def quiet_moves(self, bitboards: StackedBitboard) -> List[Move]:
        c = self.color
        knights = bitboards[self]
        other_occupancy = bitboards[~c]
        unoccupied = ~(bitboards[c] | other_occupancy)
        moves = []
        for knight_bb in lsb(knights):
            _from = next(iter_bitscan_forward(knight_bb))
            move_set = KING_ATTACKS[_from] & unoccupied
            for _to in iter_bitscan_forward(move_set):
                moves.append(Move(_from=_from, _to=_to, flags=MoveFlags.QUIET))


class Enpassant(Piece):
    _type = PieceType.ENPASSANT

    def captures(self):
        return []

    def quiet_moves(self):
        return []
