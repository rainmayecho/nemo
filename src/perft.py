from sys import argv

from nemo.core.constants import STARTING_FEN
from nemo.core.perft import perft
from nemo.core.utils import SectionProfiler

if __name__ == "__main__":
    while True:
        # depth = input("Depth: ")
        fen = input("FEN:") or STARTING_FEN
        # with SectionProfiler():
        for depth in range(1, 7):
            n = perft(int(depth), fen=fen)
            print(f"depth={depth} fen={fen}:\n{n}")
        print("\n")
