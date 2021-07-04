from .types import INV_PIECE_TYPE_MAP, Squares, PieceType
from .utils import iter_bitscan_forward, popcnt, pairwise
from .position import Position

TAG_NAME_MAP =  {
    "plycount": "PlyCount",
    "timecontrol": "TimeControl",
    "fen": "FEN"
}

class PGNWriter:
    tags = (
        ("event", "N/A"),
        ("site", "N/A"),
        ("date", "N/A"),
        ("round", "N/A"),
        ("black", "N/A"),
        ("white", "N/A"),
        ("result", "N/A"),
        ("annotator", "N/A"),
        ("plycount", "N/A"),
        ("timecontrol", "N/A"),
        ("time", "N/A"),
        ("termination", "N/A"),
        ("mode", "N/A"),
        ("fen", "N/A"),
    )
    def __init__(self, position: "Position", **tags):
        self.__position = position
        for tag, value in tags.items():
            setattr(self, tag.lower(), value)
        self.fen = position.fen

    @staticmethod
    def to_san(move: "Move", piece: "Piece", position: "Position") -> str:
        position_suffix = ""
        if position.is_check():
            position_suffix = "+"
        elif position.is_checkmate():
            position_suffix = "#"

        if move.is_castle_kingside:
            return f"O-O{position_suffix}"
        elif move.is_castle_queenside:
            return f"O-O-O{position_suffix}"
        else:
            piece_str = INV_PIECE_TYPE_MAP.get(piece._type).upper() if piece._type != PieceType.PAWN else ""
            piece_bb = position.boards.board_for(piece)
            ranks, files = set(), set()
            n = popcnt(piece_bb)
            for psq in iter_bitscan_forward(piece_bb):
                f, r = Squares(psq).name.lower()
                files.add(f)
                ranks.add(r)

            disambiguation_str = ""
            if n < 2:
                return f"{piece_str}{move.san_suffix}{position_suffix}"
            elif n >= 2 and len(ranks) == 1:
                disambiguation_str = Squares(move._from).name.lower()[0]
            elif n >= 2 and len(files) == 1:
                disambiguation_str = Squares(move._from).name.lower()[1]

            return f"{piece_str}{disambiguation_str}{move.san_suffix}{position_suffix}"

    def itermoves(self):
        it = iter(self.__position.state)
        ply = self.__position.state.ply
        p = Position(fen=next(it).fen)

        for i, states in enumerate(pairwise(it)):
            first, second = states
            move = first.move
            suffix = move.san_suffix
            piece, _from = p.make_move(move)
            san_str = self.to_san(move, piece, p)
            if second is None:
                yield f"{i + 1}. {san_str} "
            else:
                move = second.move
                piece, _from = p.make_move(move)
                second_san_str = self.to_san(move, piece, p)
                yield f"{i + 1}. {san_str} {second_san_str}"

    def itertags(self):
        for tag, default in self.tags:
            yield tag, getattr(self, tag, default)

    def write(self):
        tag_text = "\n".join(f'[{TAG_NAME_MAP.get(k, k.capitalize())} "{v}"]' for k, v in self.itertags())
        move_text =  " ".join(self.itermoves())
        return "\n".join([tag_text, "", move_text])

