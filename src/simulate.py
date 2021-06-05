from nemo.core.search import negamax
from nemo.core.position import Position

def run(n=40):
    p = Position()
    for _ in range(n):
        score, move = negamax(p, 7)
        print(f"Evaluation = {score}")
        p.make_move(move)
        print(p)
        input() 


if __name__ == "__main__":
    run()