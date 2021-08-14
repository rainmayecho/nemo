from nemo.core.search import Searcher
from nemo.core.position import Position
from nemo.core.game import Game
from nemo.core.transposition import TTable, Killers


def run(n=80):
    p = Position(fen="r2r3k/ppp3pp/8/b5N1/2Q5/8/5PP1/6K1 w - - 0 1")
    print(p)
    searcher = Searcher()
    searcher.search(p, depth=8)


if __name__ == "__main__":
    run()