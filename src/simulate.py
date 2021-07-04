from nemo.core.search import negamax
from nemo.core.position import Position
from nemo.core.game import Game

def run(n=40):
    p = Position()
    for _ in range(n):
        score, move = negamax(p, 5)
        print(f"Evaluation = {score}")
        p.make_move(move)
        print(p)
        # print(list(p.legal_moves))
        # input()
    g = Game(position=p)
    print(g.pgn)


if __name__ == "__main__":
    run()