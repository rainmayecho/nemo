from nemo.core.constants import STARTING_FEN
from nemo.core.evaluation import see
from nemo.core.position import Position
from nemo.core.search import get_ordered_moves


def run():
    p = Position(fen=input("FEN: ") or STARTING_FEN)
    print(p)
    for move in p.legal_moves:
        print(move, see(p, move))

    print(get_ordered_moves(p, 0))




if __name__ == "__main__":
    run()