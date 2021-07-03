from collections import defaultdict
from typing import Callable, Dict, List, Generator, Tuple, Optional

from .types import (
    AbstractPiece as Piece,
    Bitboard,
    Color,
    PieceType,
    Square,
    State,
    ATTACKERS,
    SLIDERS,
    CAN_CHECK,
    MOVABLE,
    EMPTY,
    PIECE_REGISTRY,
)
from .utils import (
    bitscan_forward,
    iter_bitscan_forward,
    popcnt,
)

from .zobrist import ZOBRIST_KEYS

DEFAULT_FACTORY = lambda c, p: PIECE_REGISTRY[p](c)


def test_state(c: Color):
    return State(c, "-")


class PieceCache(dict):
    """Caches piece instances"""

    def __init__(self, factory: Callable = None):
        self.__factory = factory or DEFAULT_FACTORY

    def __missing__(self, key) -> Piece:
        self[key] = self.__factory(*key)
        return self[key]


class StackedBitboard:
    __piece_cache = PieceCache()

    def __init__(self, bitboards_by_color_and_type, square_occupancy):
        self.__boards = bitboards_by_color_and_type
        self.__color_occupancy = [
            self.__white_occupancy(),
            self.__black_occupancy(),
        ]
        self.__square_occupancy = square_occupancy
        self.__attack_sets = None
        self.__initialize_attack_sets()

        # create pinned pieces bitboard for both colors
        self.__pin_sets = None
        self.__initialize_pin_sets()

        self.__check_sets = None
        self.__checkmated = None
        self.__initialize_check_sets()

    @classmethod
    def test_piece(cls, c: Color, piece_type: PieceType) -> Piece:
        return cls.__piece_cache[(c, piece_type)]

    def __initialize_attack_sets(self) -> None:
        attack_sets = {Color.WHITE: {}, Color.BLACK: {}}
        for c in self.__boards:
            for piece_type in ATTACKERS:
                attack_sets[c][piece_type] = self.test_piece(
                    c, piece_type
                ).attack_set_empty(self)
        self.__attack_sets = attack_sets

    def __initialize_pin_sets(self) -> None:
        self.__compute_pin_set()

    def __compute_pin_set(self) -> None:
        pin_sets = {Color.WHITE: Bitboard(0), Color.BLACK: Bitboard(0)}
        for c in self.__boards:
            king_bb = self.king_bb(c)
            king_square = bitscan_forward(king_bb)
            for piece_type in {PieceType.BISHOP, PieceType.ROOK}:
                for square in iter_bitscan_forward(self.__boards[~c][piece_type]):
                    pin_sets[c] |= self.__test_pin_set(
                        c, piece_type, king_bb, king_square, square
                    )

                # Queen
                for square in iter_bitscan_forward(self.__boards[~c][PieceType.QUEEN]):
                    pin_sets[c] |= self.__test_pin_set(
                        c, piece_type, king_bb, king_square, square
                    )

        self.__pin_sets = pin_sets

    def __test_pin_set(
        self,
        c: Color,
        piece_type: PieceType,
        king_bb: Bitboard,
        king_square: Square,
        piece_square: Square,
    ):
        # check king contact
        piece = self.test_piece(~c, piece_type)
        king_contact_bb = (
            piece.__class__._attack_lookup(piece_square, self.by_color(~c)) & king_bb
        )

        # replace king as enemy piece
        king_attack_set_bb = piece.__class__._attack_lookup(
            king_square, self.occupancy
        ) & self.by_color(c)

        # attackset of current piece
        piece_attack_set_bb = piece.__class__._attack_lookup(
            piece_square, self.occupancy
        ) & self.by_color(c)

        if king_contact_bb:
            return king_attack_set_bb & piece_attack_set_bb

        return 0

    def pinned_bb(self, c: Color) -> Bitboard:
        return self.__pin_sets[c]

    def attacks_by_color(self, c: Color) -> Bitboard:
        attack_bb = EMPTY
        for piece_bb in self.__attack_sets[c].values():
            attack_bb |= piece_bb
        return attack_bb

    def __compute_checkers(self, c: Color) -> Bitboard:
        """Bitboard representing pieces that can check the King of color `c`"""
        checkers_bb = EMPTY
        king_bb = self.__boards[c][PieceType.KING]
        for piece, piece_bb in self.iter_check_candidates(~c):
            for s in iter_bitscan_forward(piece_bb):
                if piece.attack_set_on(self, s) & king_bb:
                    checkers_bb |= 1 << s
        return checkers_bb

    def __initialize_check_sets(self) -> None:
        """Bitboard representing pieces that can check the King of color `c`"""
        self.__check_sets = {
            Color.WHITE: self.__compute_checkers(Color.WHITE),
            Color.BLACK: self.__compute_checkers(Color.BLACK),
        }

    def king_in_check(self, c: Color) -> bool:
        return self.__check_sets[c] != EMPTY

    def king_in_double_check(self, c: Color) -> bool:
        return popcnt(self.__check_sets[c]) == 2

    def checkers(self, c: Color) -> Bitboard:
        return self.__check_sets[c]

    def is_checkmate(self):
        return self.__checkmated is not None

    def __white_occupancy(self) -> Bitboard:
        occ = EMPTY
        for piece_type, bb in self.__boards[Color.WHITE].items():
            if piece_type != PieceType.ENPASSANT:
                occ |= bb
        return occ

    def __black_occupancy(self) -> Bitboard:
        occ = EMPTY
        for piece_type, bb in self.__boards[Color.BLACK].items():
            if piece_type != PieceType.ENPASSANT:
                occ |= bb
        return occ

    @property
    def occupancy(self) -> Bitboard:
        return self.by_color(Color.WHITE) | self.by_color(Color.BLACK)

    @property
    def squares(self) -> List[Piece]:
        return self.__square_occupancy

    @property
    def boards(self) -> Dict[Color, Dict[PieceType, Bitboard]]:
        return self.__boards

    def piece_at(self, s: Square) -> Piece:
        return self.squares[s]

    def board_for(self, p: Piece) -> Bitboard:
        return self.__boards[p.color][p._type]

    def by_color(self, c: Color) -> Bitboard:
        return self.__color_occupancy[c]

    def king_bb(self, c: Color) -> Bitboard:
        return self.__boards[c][PieceType.KING]

    def get_king(self, c: Color) -> Piece:
        s = bitscan_forward(self.__boards[c][PieceType.KING])
        return self.__square_occupancy[s]

    def move_piece(
        self, _from: int, _to: int, p: Piece, drop: Piece = None
    ) -> Optional[Piece]:
        _from, _to = Square(_from), Square(_to)
        _from_bb = _from.bitboard
        _to_bb = _to.bitboard
        _from_to_bb = _from_bb | _to_bb
        captured = self.piece_at(_to)
        if p is None:
            print(self)
            input()
        c = p.color

        if captured is not None:  # need to toggle the square on the piece bb
            _type = captured._type
            self.__boards[~c][_type] ^= _to_bb
            self.__color_occupancy[~c] ^= _to_bb
            self.__attack_sets[~c][_type] = self.test_piece(~c, _type).attack_set_empty(
                self
            )

        if drop is not None:
            _type = drop._type
            self.__boards[~c][_type] ^= _from_bb
            self.__color_occupancy[~c] ^= _from_bb
            self.__attack_sets[~c][_type] = self.test_piece(~c, _type).attack_set_empty(
                self
            )

        self.__boards[c][p._type] ^= _from_to_bb
        self.__color_occupancy[c] ^= _from_to_bb
        self.__attack_sets[c][p._type] = self.test_piece(c, p._type).attack_set_empty(
            self
        )

        self.squares[_to] = p
        self.squares[_from] = drop

        # recalculate pinned pieces
        self.__compute_pin_set()
        self.__check_sets[~c] = self.__compute_checkers(~c)
        return captured

    def place_piece(self, s: Square, p: Piece) -> None:
        if not isinstance(s, Square):
            s = Square(s)
        existing_piece_at_s = self.piece_at(s)
        placing_piece_bb = self.board_for(p)
        c = p.color
        s_bb = s.bitboard
        if existing_piece_at_s is not None:
            _type = existing_piece_at_s._type
            self.__boards[~c][_type] ^= s_bb
            self.__color_occupancy[~c] ^= s_bb
            self.__attack_sets[~c][_type] = self.test_piece(~c, _type).attack_set_empty(
                self
            )

        self.__boards[c][p._type] ^= s_bb  # Set the bit for the new piece
        self.__color_occupancy[c] ^= s_bb
        self.__attack_sets[c][p._type] = self.test_piece(c, p._type).attack_set_empty(
            self
        )

        self.squares[s] = p

        # recalculate pinned pieces
        self.__compute_pin_set()
        self.__check_sets[~c] = self.__compute_checkers(~c)
        return existing_piece_at_s

    def remove_piece(self, s: Square) -> None:
        if not isinstance(s, Square):
            s = Square(s)
        existing_piece_at_s = self.piece_at(s)
        s_bb = s.bitboard
        if existing_piece_at_s is not None:
            c = existing_piece_at_s.color
            _type = existing_piece_at_s._type
            self.__boards[c][_type] ^= s_bb
            self.__color_occupancy[c] ^= s_bb
            self.__attack_sets[c][_type] = self.test_piece(c, _type).attack_set_empty(
                self
            )
        self.squares[s] = None

        # recalculate pinned pieces
        self.__compute_pin_set()
        return existing_piece_at_s

    def toggle_enpassant_board(self, c: Color, s: Square = None) -> None:
        bb = s.bitboard if s is not None else EMPTY
        self.__boards[c][PieceType.ENPASSANT] = bb

    def ep_board(self, c: Color) -> Bitboard:
        return self.__boards[c][PieceType.ENPASSANT]

    def iterpieces(self, c: Color) -> Generator[Piece, None, None]:
        for piece_type in MOVABLE:
            yield self.test_piece(c, piece_type)

    def iter_check_candidates(self, c: Color) -> Generator[Piece, None, None]:
        for piece_type in CAN_CHECK:
            piece_bb = self.__boards[c][piece_type]
            if piece_bb:
                yield self.test_piece(c, piece_type), piece_bb

    def iter_material(
        self, c: Color
    ) -> Generator[Tuple[PieceType, Bitboard, Bitboard], None, None]:
        for piece_type in CAN_CHECK:
            yield piece_type, self.__boards[c][piece_type], self.__boards[~c][
                piece_type
            ]

    def iter_attacks(
        self, c: Color
    ) -> Generator[Tuple[PieceType, Bitboard, Bitboard], None, None]:
        for piece_type in MOVABLE:
            yield piece_type, self.__attack_sets[c][piece_type], self.__attack_sets[~c][
                piece_type
            ]

    def __hash__(self) -> int:
        h = 0
        for s, p in enumerate(self.__square_occupancy):
            if p is not None:
                h ^= ZOBRIST_KEYS[p.zobrist_index][s]
        return h
