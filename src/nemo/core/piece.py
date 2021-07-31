from abc import ABC, abstractmethod
from functools import reduce
from operator import ior
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
    EMPTY,
    PIECE_REGISTRY,
    PIECE_SYMBOL_MAP,
    RANKS,
    UNIVERSE,
    Bitboard,
    Color,
    AbstractPiece,
    PieceType,
    Ranks,
    Files,
    State,
    Square,
)
from .stacked_bitboard import StackedBitboard
from .utils import bitscan_forward, file_mask, iter_bitscan_forward, iter_lsb, lsb
from .zobrist import ZOBRIST_KEYS


class Piece(AbstractPiece):
    _type = "Piece"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zobrist_index = self._type + (6 * self.color) - 1

    def captures(
        self, bitboards: StackedBitboard, checks_bb: Bitboard = UNIVERSE, state: State = None
    ) -> List[Move]:
        return [
            *self._captures(
                self.color, bitboards.board_for(self), bitboards, checks_bb=checks_bb, state=state
            )
        ]

    def quiet_moves(
        self, bitboards: StackedBitboard, checks_bb: Bitboard = UNIVERSE, state: State = None
    ) -> List[Move]:
        return [
            *self._quiet_moves(
                self.color, bitboards.board_for(self), bitboards, checks_bb=checks_bb, state=state
            )
        ]

    def pseudo_legal_moves(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        return [*self.captures(bitboards, state=state), *self.quiet_moves(bitboards, state=state)]

    def legal_moves(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        if bitboards.king_in_double_check(self.color):
            return (
                [*self.quiet_moves(bitboards, state=state)] if self._type == PieceType.KING else []
            )
        checks_bb = bitboards.checkers(self.color)
        return [
            *self.captures(bitboards, checks_bb=checks_bb, state=state),
            *self.quiet_moves(bitboards, checks_bb=checks_bb, state=state),
        ]

    def legal_captures(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        if bitboards.king_in_double_check(self.color):
            return []
        checks_bb = bitboards.checkers(self.color)
        return [*self.captures(bitboards, checks_bb=checks_bb, state=state)]

    def legal_quiet(self, bitboards: StackedBitboard, state: State) -> List[Move]:
        checks_bb = bitboards.checkers(self.color)
        return [*self.quiet_moves(bitboards, checks_bb=checks_bb, state=state)]


    def attack_set_empty(self, bitboards: StackedBitboard, *args) -> Bitboard:
        return self._attack_set_empty(self.color, bitboards.board_for(self), bitboards, *args)

    def attack_set(self, bitboards: StackedBitboard) -> Bitboard:
        return self._attack_set(self.color, bitboards.board_for(self), bitboards)

    def attack_set_on(self, bitboards: StackedBitboard, s: Square) -> Bitboard:
        return self._attack_set(self.color, bitboards.board_for(self), bitboards, Bitboard(1 << s))

    def defend_set_empty(self, bitboards: StackedBitboard, s: Square) -> Bitboard:
        return self._defend_set(self.color, bitboards.board_for(self), bitboards, Bitboard(1 << s))

    @staticmethod
    def get_pin_mask(c: Color, _from: Square, bitboards: StackedBitboard) -> Bitboard:
        king_sq = bitscan_forward(bitboards.king_bb(c))
        return (
            Magic.get_pin_mask(king_sq, _from)
            if Square(_from).bitboard & bitboards.pinned_bb(c)
            else UNIVERSE
        )

    @staticmethod
    def get_check_mask(c: Color, checks_bb: Bitboard, bitboards: StackedBitboard) -> Bitboard:
        king_sq = bitscan_forward(bitboards.king_bb(c))
        return Magic.get_ray_mask(king_sq, bitscan_forward(checks_bb)) if checks_bb else UNIVERSE


class Enpassant(Piece):
    _type = PieceType.ENPASSANT

    @staticmethod
    def _attack_set_empty(*args, **kwargs):
        return Bitboard(0)

    def captures(self, *args):
        return []

    def quiet_moves(self, *args):
        return []


class Pawn(Piece):
    _type = PieceType.PAWN

    @staticmethod
    def _attack_set_empty(
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, s_bb: Bitboard = UNIVERSE
    ) -> Bitboard:
        return PAWN_ATTACKS[c](pawns & s_bb)

    @staticmethod
    def _attack_set(
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        occ = bitboards.by_color(~c) | bitboards.ep_board(~c)
        return PAWN_ATTACKS[c](pawns & s_bb) & occ & target

    @staticmethod
    def _defend_set(
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        occ = bitboards.by_color(c) | bitboards.ep_board(c)
        return PAWN_ATTACKS[c](pawns & s_bb) & occ & target

    @staticmethod
    def _captures(
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, checks_bb: Bitboard, state: State
    ) -> Generator[Move, None, None]:
        other_ep_board = bitboards.ep_board(~c)
        other_occupancy = bitboards.by_color(~c) | other_ep_board
        king_sq = bitscan_forward(bitboards.king_bb(c))

        forced_attack_set = UNIVERSE if checks_bb == EMPTY else checks_bb

        for pawn_bb in iter_lsb(pawns):
            _from = next(iter_bitscan_forward(pawn_bb))
            pin_mask = Piece.get_pin_mask(c, _from, bitboards)
            attack_set = PAWN_ATTACKS[c](pawn_bb) & other_occupancy & pin_mask & forced_attack_set
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
        c: Color, pawns: Bitboard, bitboards: StackedBitboard, checks_bb: Bitboard, state: State
    ) -> Generator[Move, None, None]:
        occupancy, other_occupancy = bitboards.by_color(c), bitboards.by_color(~c)

        occupied_bb = occupancy | other_occupancy
        empty = ~occupied_bb

        king_sq = bitscan_forward(bitboards.king_bb(c))
        pawns_not_pinned = pawns & ~(pawns & bitboards.pinned_bb(c) & ~(file_mask(king_sq)))

        single_push_candidates = relative_south(c, empty) & pawns_not_pinned
        empty_r3 = relative_south(c, empty & relative_fourth_rank_bb(c)) & empty
        double_push_candidates = relative_south(c, empty_r3) & pawns_not_pinned

        single_pawn_pushes = PAWN_SINGLE_PUSHES[c](single_push_candidates)
        double_pawn_pushes = PAWN_DOUBLE_PUSHES[c](double_push_candidates)
        promotions = single_pawn_pushes & relative_eigth_rank_bb(c)
        single_pawn_pushes = single_pawn_pushes & ~promotions

        SINGLE_PUSH_DIR = NORTH if c == Color.WHITE else SOUTH
        DOUBLE_PUSH_DIR = SINGLE_PUSH_DIR * 2

        check_mask = Piece.get_check_mask(c, checks_bb, bitboards)

        for _to in iter_bitscan_forward(promotions & check_mask):
            _from = _to - SINGLE_PUSH_DIR
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_N)
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_Q)
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_R)
            yield Move(_from=_from, _to=_to, flags=MoveFlags.PROMOTION_B)

        for _to in iter_bitscan_forward(double_pawn_pushes & check_mask):
            yield Move(_from=_to - DOUBLE_PUSH_DIR, _to=_to, flags=MoveFlags.DOUBLE_PAWN_PUSH)

        for _to in iter_bitscan_forward(single_pawn_pushes & check_mask):
            yield Move(_from=_to - SINGLE_PUSH_DIR, _to=_to, flags=MoveFlags.QUIET)


class Knight(Piece):
    _type = PieceType.KNIGHT

    @staticmethod
    def _attack_set_empty(
        c: Color, knights: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE
    ) -> Bitboard:
        return reduce(
            ior, (KNIGHT_ATTACKS[_from] for _from in iter_bitscan_forward(knights & s_bb)), EMPTY
        )

    @staticmethod
    def _attack_set(
        c: Color, knights: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        return reduce(
            ior, (KNIGHT_ATTACKS[_from] for _from in iter_bitscan_forward(knights & s_bb)), EMPTY
        ) & bitboards.by_color(~c) & target


    @staticmethod
    def _defend_set(
        c: Color, knights: Bitboard, bitboards: StackedBitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        return reduce(
            ior, (KNIGHT_ATTACKS[_from] for _from in iter_bitscan_forward(knights & s_bb)), EMPTY
        ) & bitboards.by_color(c) & target

    @staticmethod
    def _captures(
        c: Color, knights: Bitboard, bitboards: StackedBitboard, checks_bb: Bitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        forced_attack_set = UNIVERSE if checks_bb == EMPTY else checks_bb

        for _from in iter_bitscan_forward(knights):
            if Square(_from).bitboard & bitboards.pinned_bb(c):
                continue
            attack_set = KNIGHT_ATTACKS[_from] & other_occupancy & forced_attack_set
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @staticmethod
    def _quiet_moves(
        c: Color, knights: Bitboard, bitboards: StackedBitboard, checks_bb: Bitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        unoccupied = ~(bitboards.by_color(c) | other_occupancy)
        check_mask = Piece.get_check_mask(c, checks_bb, bitboards)

        for _from in iter_bitscan_forward(knights):
            if Square(_from).bitboard & bitboards.pinned_bb(c):
                continue
            jump_set = KNIGHT_ATTACKS[_from] & unoccupied & check_mask
            for _to in iter_bitscan_forward(jump_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.QUIET)


class King(Piece):
    _type = PieceType.KING

    @staticmethod
    def _attack_set_empty(
        c: Color, king: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE
    ) -> Bitboard:
        return reduce(
            ior, (KING_ATTACKS[_from] for _from in iter_bitscan_forward(king & s_bb)), EMPTY
        )

    @staticmethod
    def _attack_set(
        c: Color, king: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        return reduce(
            ior, (KING_ATTACKS[_from] for _from in iter_bitscan_forward(king & s_bb)), EMPTY
        ) & bitboards.by_color(~c) & target

    @staticmethod
    def _defend_set(
        c: Color, king: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        return reduce(
            ior, (KING_ATTACKS[_from] for _from in iter_bitscan_forward(king & s_bb)), EMPTY
        ) & bitboards.by_color(c) & target


    @staticmethod
    def _captures(
        c: Color, kings: Bitboard, bitboards: StackedBitboard, checks_bb: Bitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        unattacked = ~(bitboards.attacks_by_color(~c))

        attack_set = UNIVERSE

        for _from in iter_bitscan_forward(kings):
            attack_set &= KING_ATTACKS[_from] & other_occupancy & unattacked
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @staticmethod
    def _quiet_moves(
        c: Color, king_bb: Bitboard, bitboards: StackedBitboard, checks_bb: Bitboard, state: State
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        unoccupied = ~(bitboards.by_color(c) | other_occupancy)
        unattacked = ~(bitboards.attacks_by_color(~c))
        _from = bitscan_forward(king_bb)
        move_set = KING_ATTACKS[_from] & unoccupied & unattacked
        for _to in iter_bitscan_forward(move_set):
            yield Move(_from=_from, _to=_to, flags=MoveFlags.QUIET)

        castling_rights = state.castling_rights[c]
        if castling_rights and ((1 << _from) & Files.E) and checks_bb == EMPTY:
            krsq = relative_rook_squares(c, short=True)[0]
            qrsq = relative_rook_squares(c, short=False)[0]

            ks_mask = 6 << (krsq - 3)
            qs_mask = 7 << (qrsq + 1)
            unattacked_qs = ((qs_mask ^ lsb(qs_mask)) & unattacked) == (3 << (qrsq + 2))

            oo_clear = (ks_mask & unoccupied & unattacked) == ks_mask
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
                and unattacked_qs
                and qr
                and qr._type == PieceType.ROOK
                and qr.color == c
            ):
                yield Move(_from, qrsq + 2, flags=MoveFlags.QUEENSIDE_CASTLE)


# SLIDING PIECES


class SlidingPiece(Piece):
    _attack_lookup = lambda s: 0

    @classmethod
    def _attack_set_empty(
        cls, c: Color, piece_bb: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE
    ) -> Bitboard:
        blockers = (bitboards.by_color(c) | bitboards.by_color(~c)) & ~(bitboards.king_bb(~c))
        attack_set = Bitboard(0)
        for _from in iter_bitscan_forward(piece_bb & s_bb):
            attack_set |= cls._attack_lookup(_from, blockers)
        return attack_set

    @classmethod
    def _attack_set(
        cls, c: Color, piece_bb: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        blockers = bitboards.by_color(c) | bitboards.by_color(~c)
        attack_set = Bitboard(0)
        for _from in iter_bitscan_forward(piece_bb & s_bb):
            attack_set |= cls._attack_lookup(_from, blockers)
        return attack_set & bitboards.by_color(~c) & target

    @classmethod
    def _defend_set(
        cls, c: Color, piece_bb: Bitboard, bitboards: Bitboard, s_bb: Bitboard = UNIVERSE, target: Bitboard = UNIVERSE
    ) -> Bitboard:
        blockers = bitboards.by_color(c) | bitboards.by_color(~c)
        attack_set = Bitboard(0)
        for _from in iter_bitscan_forward(piece_bb & s_bb):
            attack_set |= cls._attack_lookup(_from, blockers)
        return attack_set & bitboards.by_color(c) & target

    @classmethod
    def _captures(
        cls,
        c: Color,
        piece_bb: Bitboard,
        bitboards: StackedBitboard,
        checks_bb: Bitboard,
        state: State,
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        blockers = bitboards.by_color(c) | other_occupancy

        forced_attack_set = UNIVERSE if checks_bb == EMPTY else checks_bb

        for _from in iter_bitscan_forward(piece_bb):
            pin_mask = Piece.get_pin_mask(c, _from, bitboards)
            attack_set = cls._attack_lookup(_from, blockers) & other_occupancy & pin_mask & forced_attack_set
            for _to in iter_bitscan_forward(attack_set):
                yield Move(_from=_from, _to=_to, flags=MoveFlags.CAPTURES)

    @classmethod
    def _quiet_moves(
        cls,
        c: Color,
        piece_bb: Bitboard,
        bitboards: StackedBitboard,
        checks_bb: Bitboard,
        state: State,
    ) -> Generator[Move, None, None]:
        other_occupancy = bitboards.by_color(~c)
        blockers = bitboards.by_color(c) | other_occupancy

        check_mask = Piece.get_check_mask(c, checks_bb, bitboards)

        for _from in iter_bitscan_forward(piece_bb):
            pin_mask = Piece.get_pin_mask(c, _from, bitboards)
            attack_set = cls._attack_lookup(_from, blockers) & ~blockers & pin_mask & check_mask
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
