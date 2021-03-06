from collections import defaultdict

from .constants import STARTING_FEN
from .piece import Piece
from .types import (
    Bitboard,
    Color,
    PieceType,
    PIECE_REGISTRY,
    PROMOTABLE,
    Square,
    Squares,
    StackedBitboard,
    State,
)
from .move import Move
from .move_gen import relative_rook_squares, square_above, square_below


class Position:
    def __init__(self, fen=STARTING_FEN):
        self.clear()
        if fen is not None:
            self.from_fen(fen)

    def clear(self):
        self.__boards = None
        self.__state = None

    def from_fen(self, fen):
        ranks, turn, castling_rights, ep_square, hmc, fmc = fen.split(" ")
        i = 0
        rows = ranks.split("/")[::-1]
        boards = defaultdict(lambda: defaultdict(lambda: Bitboard(0)))
        square_occupancy = [None] * 64

        if ep_square != "-":
            square = Squares[ep_square.upper()]
            c = Color.WHITE if square._value_ < 32 else Color.BLACK
            piece_type = PIECE_REGISTRY["ep"]._type
            boards[c][piece_type] |= square.bitboard
            boards[~c][piece_type] = Bitboard(0)
        else:
            piece_type = PIECE_REGISTRY["ep"]._type
            boards[Color.WHITE][piece_type] = Bitboard(0)
            boards[Color.BLACK][piece_type] = Bitboard(0)

        for i, row in enumerate(rows):
            j = 0
            for c in row:
                if not c.isdigit():
                    color = Color.WHITE if c.isupper() else Color.BLACK
                    piece = PIECE_REGISTRY[c.lower()](color)
                    idx = i * 8 + j
                    bb = boards[color][piece._type] | (1 << idx)
                    square_occupancy[idx] = piece
                    boards[color][piece._type] |= bb
                    j += 1
                else:
                    j += int(c)
        self.__boards = StackedBitboard(boards, square_occupancy)
        self.__state = State(
            turn,
            castling_rights,
            ep_square,
            hmc,
            fmc,
        )

    @property
    def pseudo_legal_moves(self):
        c = self.state.turn
        for test_piece in self.boards.iterpieces(c):
            yield from iter(test_piece.pseudo_legal_moves(self.bitboards, self.state))

    def is_legal(self):
        return not self.boards.king_in_check(~self.state.turn)

    def make_move(self, move: Move) -> None:
        _from, _to = move
        color = self.state.turn
        captured = None
        piece = self.boards.piece_at(_from)
        # assert piece is not None
        if move.is_enpassant_capture:
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)
            captured = self.boards.remove_piece(square_below(_to, color))
        elif move.is_double_pawn_push:
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)
        elif move.is_promotion:
            promotion_piece = PIECE_REGISTRY[move.promotion_piece_type](color)
            self.boards.remove_piece(_from)
            captured = self.boards.place_piece(_to, promotion_piece)
        elif move.is_capture:
            self.boards.remove_piece(_from)
            captured = self.boards.place_piece(_to, piece)
        elif move.is_castle_kingside or move.is_castle_queenside:
            king = piece
            r_from, r_to = relative_rook_squares(color, short=move.is_castle_kingside)
            self.boards.remove_piece(_from)  # remove king
            rook = self.boards.remove_piece(r_from)  # remove appropriate rook
            self.boards.place_piece(_to, king)  # place king
            self.boards.place_piece(r_to, rook)  # place rook
        else:
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)

        castling_rights_mask = 0
        if piece._type == PieceType.KING:
            castling_rights_mask = 3 << (2 * color)
        elif piece._type == PieceType.ROOK:
            b = int(relative_rook_squares(color, short=False)[0] == _from) + 1
            castling_rights_mask = b << (2 * color)

        ep_square = square_below(color, move.ep_square_premask)
        self.state.push(
            castling=castling_rights_mask,
            captured=captured,
            ep_square=ep_square,
        )

    def unmake_move(self, _move: Move) -> None:
        move = ~_move
        _from, _to = move
        castling, captured, ep_square = self.state.pop()
        color = self.state.turn
        piece = self.boards.piece_at(_from)
        # assert piece is not None
        if move.is_enpassant_capture:
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)
            self.boards.place_piece(square_below(_from, color), captured)
        elif move.is_double_pawn_push:
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)
        elif move.is_promotion:
            pawn = PIECE_REGISTRY["p"](self.state.turn)
            promoted = self.boards.remove_piece(_from)  # remove the promoted piece
            assert promoted._type in PROMOTABLE
            self.boards.place_piece(_to, pawn)
            if captured:
                self.boards.place_piece(_from, captured)
        elif move.is_capture:
            # assert captured is not None
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)
            self.boards.place_piece(_from, captured)
        elif move.is_castle_kingside or move.is_castle_queenside:
            king = piece
            r_to, r_from = relative_rook_squares(color, short=move.is_castle_kingside)
            self.boards.remove_piece(_from)  # remove king
            rook = self.boards.remove_piece(r_from)  # remove appropriate rook
            self.boards.place_piece(_to, king)  # place king
            self.boards.place_piece(r_to, rook)  # place rook
        else:
            # assert move.is_quiet
            self.boards.remove_piece(_from)
            self.boards.place_piece(_to, piece)

    @property
    def state(self):
        return self.__state

    @property
    def squares(self):
        return self.__boards.squares

    @property
    def bitboards(self):
        return self.__boards

    @property
    def boards(self):
        return self.__boards

    def __str__(self):
        div = "┼" + "───┼" * 8
        rows = [div]
        for i in range(8):
            row = []
            for j in range(8):
                idx = i * 8 + j
                p = self.__boards.squares[idx]
                row.append(p or " ")
            rows.append("│ " + f" │ ".join(str(p) for p in row) + " │")
            rows.append(div)
        return "\n".join(rows[::-1])


def test_pawns():
    white_pawn = PIECE_REGISTRY["p"](Color.WHITE)
    black_pawn = PIECE_REGISTRY["p"](Color.BLACK)

    p = Position()
    assert white_pawn.captures(p.bitboards) == []
    assert len(white_pawn.quiet_moves(p.bitboards)) == 16

    p = Position(fen="rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")  # pawn attacks
    assert len(white_pawn.captures(p.bitboards)) == 1
    assert str(white_pawn.captures(p.bitboards)[0]) == "e4d5"
    assert len(black_pawn.captures(p.bitboards)) == 1
    assert str(black_pawn.captures(p.bitboards)[0]) == "d5e4"

    p = Position(fen="rnbqkbnr/1pp1pppp/p7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3")  # enpassant
    assert len(white_pawn.captures(p.bitboards)) == 1
    assert str(white_pawn.captures(p.bitboards)[0]) == "e5d6"
    assert len(black_pawn.captures(p.bitboards)) == 0

    p = Position(
        fen="rnbqkbnr/1pppppPp/8/8/8/8/PpPPP1PP/RNBQKBNR w KQkq - 0 5"
    )  # captures + promotions
    assert len(white_pawn.captures(p.bitboards)) == 8
    assert len(black_pawn.captures(p.bitboards)) == 8
    assert white_pawn.captures(p.bitboards)[0].is_promotion
    assert black_pawn.captures(p.bitboards)[0].is_promotion


def test_king():
    pass


def test_pins():
    pass


def test_promotions():
    pass
