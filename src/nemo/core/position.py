from collections import defaultdict
import io

from .constants import STARTING_FEN
from .exceptions import IllegalMoveException
from .pgn import PGNWriter
from .piece import Piece
from .types import (
    Bitboard,
    Color,
    PieceAndSquare,
    PieceType,
    INV_PIECE_TYPE_MAP,
    PIECE_REGISTRY,
    PROMOTABLE,
    UNBLOCKABLE_CHECKERS,
    Square,
    Squares,
    State,
)
from .stacked_bitboard import StackedBitboard
from .magic import Magic
from .move import Move
from .move_gen import (
    e_one,
    w_one,
    relative_fourth_rank_bb,
    relative_rook_squares,
    square_above,
    square_below,
)
from .utils import bitscan_forward
from .zobrist import ZOBRIST_KEYS, ZOBRIST_CASTLE, ZOBRIST_EP, ZOBRIST_TURN

def emptyboard():
    return Bitboard(0)

def boardmaker():
    return defaultdict(emptyboard)

class Position:
    def __init__(self, fen=STARTING_FEN):
        self.clear()
        if fen:
            self.from_fen(fen)

        self.key = hash(
            self.__boards
        )  # only do this once; incremental update per move.

    def clear(self):
        self.__boards = None
        self.__state = None

    def from_fen(self, fen):
        split_fen = fen.split(" ")
        split_fen = split_fen + ["0", "1"] if len(split_fen) < 6 else split_fen
        ranks, turn, castling_rights, ep_square, hmc, fmc = split_fen
        rows = ranks.split("/")[::-1]
        boards = defaultdict(boardmaker)
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
            move=None,
            fen=fen,
        )

    @property
    def legal_moves(self):
        for test_piece in self.boards.iterpieces(self.state.turn):
            yield from iter(test_piece.legal_moves(self.bitboards, self.state))

    @property
    def legal_captures(self):
        for test_piece in self.boards.iterpieces(self.state.turn):
            yield from iter(test_piece.legal_captures(self.bitboards, self.state))

    @property
    def legal_quiet(self):
        for test_piece in self.boards.iterpieces(self.state.turn):
            yield from iter(test_piece.legal_quiet(self.bitboards, self.state))

    @property
    def pseudo_legal_moves(self):
        for test_piece in self.boards.iterpieces(self.state.turn):
            yield from iter(test_piece.pseudo_legal_moves(self.bitboards, self.state))

    def is_legal(self):
        return not self.boards.king_in_check(~self.state.turn)

    def is_check(self):
        return self.boards.king_in_check(self.state.turn)

    def is_double_check(self):
        return self.boards.king_in_double_check(self.state.turn)

    def is_checkmate(self):
        return self.is_check() and len(list(self.legal_moves)) == 0
        # c = self.state.turn
        # ksq = self.boards.get_king_square(c)
        # king = self.boards.piece_at(ksq)
        # king_moves = list(king.legal_moves(self.bitboards, self.state))
        # can_move = len(king_moves) > 0
        # if can_move:
        #     return False
        # elif self.is_double_check():
        #     return not can_move
        # elif self.is_check():
        #     check_bb, checking_piece, s = self.boards.get_checker(c)
        #     attack_bb = self.boards.attacks_by_color(c)
        #     can_capture = bool(attack_bb & check_bb)

        #     can_block = 1
        #     if checking_piece._type in UNBLOCKABLE_CHECKERS:
        #         can_block = 0
        #     else:
        #         can_block = attack_bb & Magic.get_ray_mask(ksq, bitscan_forward(check_bb))
        #     if can_block or can_capture:
        #         return False
        #     return True
        # return False

    def make_move(self, move: Move, details=False) -> PieceAndSquare:
        _from, _to = move
        color = self.state.turn
        captured = None
        promotion_piece = None
        ep_square = None
        piece = self.boards.piece_at(_from)
        fen = self.fen
        # assert piece is not None
        if move.is_enpassant_capture:
            self.boards.move_piece(_from, _to, piece)
            captured = self.boards.remove_piece(square_below(color, _to))
            self.boards.toggle_enpassant_board(~color)
        elif move.is_double_pawn_push:
            other_king_bb_on_fifth = self.boards.king_bb(
                ~color
            ) & relative_fourth_rank_bb(color)
            _to_bb = Square(_to).bitboard
            adj_bb = e_one(_to_bb) | w_one(_to_bb)
            ep_square = square_below(color, _to)
            if not (
                other_king_bb_on_fifth and (adj_bb & self.boards.pinned_bb(~color))
            ):
                self.boards.toggle_enpassant_board(color, ep_square)
            self.boards.move_piece(_from, _to, piece)
        elif move.is_promotion:
            promotion_piece = PIECE_REGISTRY[move.promotion_piece_type](color)
            self.boards.remove_piece(_from)
            captured = self.boards.place_piece(_to, promotion_piece)
        elif move.is_capture:
            captured = self.boards.move_piece(_from, _to, piece)
        elif move.is_castle_kingside or move.is_castle_queenside:
            king = piece
            r_from, r_to = relative_rook_squares(color, short=move.is_castle_kingside)
            self.boards.move_piece(_from, _to, king)
            self.boards.move_piece(r_from, r_to, self.boards.piece_at(r_from))
        else:
            self.boards.move_piece(_from, _to, piece)

        castling_rights_mask = 0
        if piece._type == PieceType.KING:
            castling_rights_mask = 3 << (2 * color)
        elif piece._type == PieceType.ROOK:
            long = int(relative_rook_squares(color, short=False)[0] == _from)
            short = int(relative_rook_squares(color, short=True)[0] == _from)
            b = int(long or short) + int(long)
            castling_rights_mask = b << (2 * color)

        pidx = getattr(piece, "zobrist_index", 12)
        cidx = getattr(captured, "zobrist_index", 12)
        ppidx = getattr(promotion_piece, "zobrist_index", pidx)
        self.boards.toggle_enpassant_board(~color)
        self.state.push(
            castling=castling_rights_mask,
            captured=captured,
            ep_square=ep_square,
            move=move,
            fen=fen
        )
        self.key ^= self.zk_xor(
            _from, _to, pidx, cidx, ppidx, self.state.castling_rights, ep_square
        )

        return PieceAndSquare(piece=piece, square=_from)


    def unmake_move(self, _move: Move) -> None:
        move = ~_move
        _from, _to = move
        castling, captured, ep_square, _, _ = self.state.pop()
        # castling, _, _ = self.state.top()
        color = self.state.turn
        piece = self.boards.piece_at(_from)

        pidx = getattr(piece, "zobrist_index", 12)
        cidx = getattr(captured, "zobrist_index", 12)
        ppidx = pidx  #  placeholder in-case of undoing promotion piece

        if move.is_enpassant_capture:
            self.boards.move_piece(_from, _to, piece)
            self.boards.toggle_enpassant_board(~color, Square(_from))
            self.boards.place_piece(square_below(color, _from), captured)
        elif move.is_double_pawn_push:
            self.boards.move_piece(_from, _to, piece)
            self.boards.toggle_enpassant_board(color)
        elif move.is_promotion:
            pawn = PIECE_REGISTRY["p"](color)
            ppidx = getattr(pawn, "zobrist_index", 12)
            promoted = self.boards.remove_piece(_from)  # remove the promoted piece
            self.boards.place_piece(_to, pawn)
            if captured:
                self.boards.place_piece(_from, captured)
        elif move.is_capture:
            self.boards.move_piece(_from, _to, piece, drop=captured)
        elif move.is_castle_kingside or move.is_castle_queenside:
            king = piece
            r_to, r_from = relative_rook_squares(color, short=move.is_castle_kingside)
            self.boards.move_piece(_from, _to, king)
            self.boards.move_piece(r_from, r_to, self.boards.piece_at(r_from))
        else:
            self.boards.move_piece(_from, _to, piece)

        self.key ^= self.undo_zk_xor(_from, _to, pidx, cidx, ppidx, castling, ep_square)

    @staticmethod
    def zk_xor(_from, _to, pidx, cidx, ppidx, castling, ep_square, debug=True):
        return (
            ZOBRIST_KEYS[pidx][_from]
            ^ ZOBRIST_KEYS[cidx][_to]
            ^ ZOBRIST_KEYS[ppidx][_to]
            ^ ZOBRIST_CASTLE[castling]
            ^ (0 if ep_square is None else ZOBRIST_EP[ep_square % 8])
            ^ ZOBRIST_TURN
        )

    @staticmethod
    def undo_zk_xor(_from, _to, pidx, cidx, ppidx, castling, ep_square, debug=True):
        return (
            ZOBRIST_KEYS[pidx][_from]
            ^ ZOBRIST_KEYS[cidx][_from]
            ^ ZOBRIST_KEYS[ppidx][_to]
            ^ ZOBRIST_CASTLE[castling]
            ^ (0 if ep_square is None else ZOBRIST_EP[ep_square % 8])
            ^ ZOBRIST_TURN
        )

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

    @property
    def fen(self):
        squares = iter(self.squares)
        rows = []
        for _ in range(8):
            rows.append([next(squares) for _ in range(8)])
        rows = rows[::-1]
        with io.StringIO() as s:
            for row in rows:
                empty = 0
                for p in row:
                    if p is not None:
                        if empty > 0:
                            s.write(str(empty))
                            empty = 0
                        c = p.color
                        w = INV_PIECE_TYPE_MAP[p._type]
                        s.write(w.upper() if c == Color.WHITE else w.lower())
                    else:
                        empty += 1
                if empty > 0:
                    s.write(str(empty))
                s.write("/")
            # Move one position back to overwrite last '/'
            s.seek(s.tell() - 1)
            # If you do not have the additional information choose what to put
            s.write(f" {self.state.fen_suffix}")
            return s.getvalue()

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
        return "\n".join(rows[::-1] + [self.fen])

    def __hash__(self) -> int:
        return self.key


def test_pawns():
    white_pawn = PIECE_REGISTRY["p"](Color.WHITE)
    black_pawn = PIECE_REGISTRY["p"](Color.BLACK)

    p = Position()
    assert white_pawn.captures(p.bitboards) == []
    assert len(white_pawn.quiet_moves(p.bitboards)) == 16

    p = Position(
        fen="rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    )  # pawn attacks
    assert len(white_pawn.captures(p.bitboards)) == 1
    assert str(white_pawn.captures(p.bitboards)[0]) == "e4d5"
    assert len(black_pawn.captures(p.bitboards)) == 1
    assert str(black_pawn.captures(p.bitboards)[0]) == "d5e4"

    p = Position(
        fen="rnbqkbnr/1pp1pppp/p7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
    )  # enpassant
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
