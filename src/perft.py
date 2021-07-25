from sys import argv
from time import time

from nemo.core.constants import STARTING_FEN
from nemo.core.perft import perft
from nemo.core.utils import SectionProfiler

if __name__ == "__main__":
    while True:
        # depth = input("Depth: ")
        fen = input("FEN:") or STARTING_FEN
        # with SectionProfiler():
        for depth in range(1, 7):
            start = time()
            n = perft(int(depth), fen=fen)
            print(f"depth={depth} fen={fen}:\n{n}")
            print(f"{(n.nodes / 1000) / (time() - start) } kN/sec")
        print("\n")
