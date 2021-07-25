from collections import deque, defaultdict
from typing import Any, List

class _TranspositionTable(dict):
    def __init__(self, max_size = 10**7):
        super().__init__()
        self.__max_size = max_size
        self.__stack = deque([])

    def __setitem__(self, key: int, value: "SearchResult") -> None:
        if len(self.__stack) >= self.__max_size:
            self.pop(self.__stack[-1], None)
            self.__stack.pop()
        self.__stack.appendleft(key)
        super().__setitem__(key, value)

    def extract_principal_variation(self, node: "Position") -> List["Move"]:
        moves = []
        before = node.key
        while node.key in self:
            move = self[node.key].move
            if move:
                node.make_move(move)
                moves.append(move)

        for move in moves[::-1]:
            node.unmake_move(move)

        assert node.key == before
        return moves

    def reset(self):
        self.clear()

    def is_full(self):
        return len(self.__stack) == self.__max_size



TTable = _TranspositionTable()
Killers = defaultdict(lambda: _TranspositionTable(max_size=2))