from .types import SQUARES, Squares


class Move:
    def __init__(self, _from: int, _to: int, promotion: int = 0, uci=None):
        if uci is not None:
            self._from = Squares[uci[0:2].upper()]
            self._to = Squares[uci[2:4].upper()]
        else:
            self._from = SQUARES[_from]
            self._to = SQUARES[_to]
        self._promotion = promotion

    @property
    def uci(self) -> str:
        return str(self)

    def __invert__(self) -> "Move":
        return type(self)(self._to, self._from)

    def __repr__(self) -> str:
        return f"<Move {self._from.name.lower()} to {self._to.name.lower()}>"

    def __str__(self) -> str:
        return f"{self._from.name.lower()}{self._to.name.lower()}"
