from nemo.core.search import Searcher
from nemo.core.position import Position
from nemo.core.game import Game
from nemo.core.transposition import TTable, Killers


def run(n=80):
    p = Position()
    print(p)
    searcher = Searcher()
    searcher.search(p, depth=8)


if __name__ == "__main__":
    run()