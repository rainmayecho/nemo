from nemo.core.search import negamax
from nemo.core.position import Position
from nemo.core.game import Game
from nemo.core.transposition import TTable, Killers


def run(n=80):
    p = Position()
    print(p)
    for d in range(n):
        result = negamax(p, min(d + 1, 8))
        TTable[p.key] = result
        print(Killers)
        print(f"PV = {' '.join(map(str, TTable.extract_principal_variation(p)))}")
        print(f"Evaluation = {result.score}")
    g = Game(position=p)
    print(g.pgn)


if __name__ == "__main__":
    run()