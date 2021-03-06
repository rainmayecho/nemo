from abc import ABC, abstractmethod
from functools import lru_cache, partial
from typing import List, Generator

from .constants import NE, NORTH, NW, SE, SOUTH, SW
from .move import Move, MoveFlags
from .move_gen import (
    BISHOP_ATTACKS,
    KING_ATTACKS,
    KNIGHT_ATTACKS,
    PAWN_ATTACKS,
    PAWN_DOUBLE_ATTACKS,
    PAWN_DOUBLE_PUSHES,
    PAWN_SINGLE_ATTACKS,
    PAWN_SINGLE_PUSHES,
    QUEEN_ATTACKS,
    ROOK_ATTACKS,
    relative_second_rank_bb,
    relative_third_rank_bb,
    relative_fourth_rank_bb,
    relative_eigth_rank_bb,
    relative_rook_squares,
    relative_south,
)
from .magic import Magic
from .types import (
    PIECE_REGISTRY,
    PIECE_SYMBOL_MAP,
    RANKS,
    Bitboard,
    Color,
    AbstractPiece,
    PieceType,
    Ranks,
    Files,
    StackedBitboard,
    State,
)
from .utils import iter_bitscan_forward, iter_lsb


class Piece(AbstractPiece):
    _type = "Piece"

    def captures(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        return [*self._captures(self.color, bitboards.board_for(self), bitboards, state)]

    def quiet_moves(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        return [*self._quiet_moves(self.color, bitboards.board_for(self), bitboards, state)]

    def pseudo_legal_moves(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        return [*self.captures(bitboards, state), *self.quiet_moves(bitboards, state)]

    def legal_moves(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        return []

    def attack_set(self, bitboards: StackedBitboard) -> Bitboard:
        return self._attack_set(self.color, bitboards.board_for(self), bitboards)


class Enpassant(Piece):
    _type = PieceType.ENPASSANT

    def attack_set(self, *args):
        return Bitboard(0)

    def captures(self, *args):
        return []

    def quiet_moves(self, *args):
        return []


class Pawn(Piece):
    _type = PieceType.PAWN

    @staticmethod
    def _attack_set(c: Color, pawns: Bitboard, bitboards: StackedBitboard) -> Bitboard:
        occ = bitboards.by_color(~c) | bitboards.ep_board(~c)
        return PAWN_ATTACKS[c](pawns) & occ

    @staticmethod
    def _captures(
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_ep_board = bitboards.ep_board(~c)
        other_occupancy = bitboards.by_color(~c) | other_ep_board
        for pawn_bb in iter_lsb(pawns):
            _from = next(iter_bitscan_forward(pawn_bb))
            attack_set = PAWN_ATTACKS[c](pawn_bb) & other_occupancy
            promotion_attack_set = attack_set & relative_eigth_rank_bb(c)
            enpassant_attack_set = attack_set & other_ep_board
            attack_set &= ~promotion_attack_set
            attack_set &= ~enpassant_attack_set

            for _to in iter_bitscan_forward(promotion_attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_Q_CAPTURE)
                yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_N_CAPTURE)
                yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_R_CAPTURE)
                yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_B_CAPTURE)

            for _to in iter_bitscan_forward(enpassant_attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.ENPASSANT_CAPTURE)

            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @staticmethod
    def _quiet_moves(
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        occupancy, other_occupancy = bitboards.by_color(c), bitboards.by_color(~c)

        occupied_bb = occupancy | other_occupancy
        unmoved_pawns = pawns & relative_second_rank_bb(c)
        empty = ~occupied_bb
        single_push_candidates = relative_south(c, empty) & pawns
        empty_r3 = relative_south(c, empty & relative_fourth_rank_bb(c)) & empty
        double_push_candidates = relative_south(c, empty_r3) & pawns

        single_pawn_pushes = PAWN_SINGLE_PUSHES[c](single_push_candidates)
        double_pawn_pushes = PAWN_DOUBLE_PUSHES[c](double_push_candidates)
        promotions = single_pawn_pushes & relative_eigth_rank_bb(c)
        single_pawn_pushes = single_pawn_pushes & ~promotions

        SINGLE_PUSH_DIR = NORTH if c == Color.WHITE else SOUTH
        DOUBLE_PUSH_DIR = SINGLE_PUSH_DIR * 2

        moves = []
        for _to in iter_bitscan_forward(promotions):
            _from = _to - SINGLE_PUSH_DIR
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_N)
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_Q)
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_R)
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_B)

        for _to in iter_bitscan_forward(double_pawn_pushes):
            yield Move(_from=_to - DOUBLE_PUSH_DIR, _to=_to, flags=MoveFlags.DOUBLE_PAWN_PUSH)

        for _to in iter_bitscan_forward(single_pawn_pushes):
            yield Move(_from=_to - SINGLE_PUSH_DIR, _to=_to, flags=MoveFlags.QUIET)

        return moves


class Knight(Piece):
    _type = PieceType.KNIGHT

    @staticmethod
    def _attack_set(c: Color, knights: Bitboard, bitboards: Bitboard) -> Bitboard:
        occ = bitboards.by_color(~c)
        attack_set = Bitboard(0)
        for knight_bb in iter_lsb(knights):
            attack_set |= KNIGHT_ATTACKS[next(iter_bitscan_forward(knight_bb))]
        return attack_set & occ

    @staticmethod
    def _captures(
        c: Color, knights: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        for knight_bb in iter_lsb(knights):
            _from = next(iter_bitscan_forward(knight_bb))
            attack_set = KNIGHT_ATTACKS[_from] & other_occupancy
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @staticmethod
    def _quiet_moves(
        c: Color, knights: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        unoccupied = ~(bitboards.by_color(c) | other_occupancy)
        for knight_bb in iter_lsb(knights):
            _from = next(iter_bitscan_forward(knight_bb))
            jump_set = KNIGHT_ATTACKS[_from] & unoccupied
            for _to in iter_bitscan_forward(jump_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.QUIET)


class King(Piece):
    _type = PieceType.KING

    @staticmethod
    def _attack_set(c: Color, kings: Bitboard, bitboards: Bitboard) -> Bitboard:
        occ = bitboards.by_color(~c)
        attack_set = Bitboard(0)
        for king_bb in iter_lsb(kings):
            attack_set |= KING_ATTACKS[next(iter_bitscan_forward(king_bb))]
        return attack_set & occ

    @staticmethod
    def _captures(
        c: Color, kings: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        for king_bb in iter_lsb(kings):
            _from = next(iter_bitscan_forward(king_bb))
            attack_set = KING_ATTACKS[_from] & other_occupancy
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @staticmethod
    def _quiet_moves(
        c: Color, king_bb: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        unoccupied = ~(bitboards.by_color(c) | other_occupancy)
        _from = next(iter_bitscan_forward(king_bb))
        move_set = KING_ATTACKS[_from] & unoccupied
        for _to in iter_bitscan_forward(move_set):
            yield Move(_from=_from, _to=_to, flags=MoveFlags.QUIET)

        castling_rights = state.castling_rights >> (c * 2)
        # if castling_rights and not ((1 << _from) & Files.E):
        #     print("castling rights are not working")
        if castling_rights and ((1 << _from) & Files.E):
            krsq = relative_rook_squares(c, short=True)[0]
            qrsq = relative_rook_squares(c, short=False)[0]

            ks_mask = 6 << krsq - 3
            qs_mask = 7 << qrsq + 1
            oo_clear = (ks_mask & unoccupied) == ks_mask
            ooo_clear = (qs_mask & unoccupied) == qs_mask

            kr = bitboards.piece_at(krsq)
            qr = bitboards.piece_at(qrsq)

            if (
                castling_rights & 1
                and oo_clear
                and kr
                and kr._type == PieceType.ROOK
                and kr.color == c
            ):
                yield Move(_from, krsq - 1, flags=MoveFlags.KINGSIDE_CASTLE)
            if (
                castling_rights & 2
                and ooo_clear
                and qr
                and qr._type == PieceType.ROOK
                and qr.color == c
            ):
                yield Move(_from, qrsq + 2, flags=MoveFlags.QUEENSIDE_CASTLE)


# SLIDING PIECES


class SlidingPiece(Piece):
    _attack_lookup = lambda s: 0

    @classmethod
    def _attack_set(cls, c: Color, piece_bb: Bitboard, bitboards: Bitboard) -> Bitboard:
        blockers = bitboards.by_color(c) | bitboards.by_color(~c)
        attack_set = Bitboard(0)
        for _from in iter_bitscan_forward(piece_bb):
            attack_set |= cls._attack_lookup(_from, blockers)
        return attack_set & bitboards.by_color(~c)

    @classmethod
    def _captures(
        cls, c: Color, piece_bb: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        blockers = bitboards.by_color(c) | other_occupancy
        for _from in iter_bitscan_forward(piece_bb):
            attack_set = cls._attack_lookup(_from, blockers) & other_occupancy
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @classmethod
    def _quiet_moves(
        cls, c: Color, piece_bb: Bitboard, bitboards: StackedBitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        blockers = bitboards.by_color(c) | other_occupancy
        for _from in iter_bitscan_forward(piece_bb):
            attack_set = cls._attack_lookup(_from, blockers) & ~blockers
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.QUIET)


class Bishop(SlidingPiece):
    _type = PieceType.BISHOP
    _attack_lookup = Magic.bishop_attacks


class Rook(SlidingPiece):
    _type = PieceType.ROOK
    _attack_lookup = Magic.rook_attacks


class Queen(SlidingPiece):
    _type = PieceType.QUEEN
    _attack_lookup = lambda s, occ: Magic.bishop_attacks(s, occ) | Magic.rook_attacks(s, occ)
