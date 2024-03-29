import asyncio
import logging
import re
import sys

from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, TimeoutError
from pprint import pprint
from threading import Event
from time import time, sleep
from typing import Any, Callable, List, Optional, TypeVar, Generic

from nemo.core.game import Game
from nemo.core.move import Move
from nemo.core.position import Position
from nemo.core.search import Searcher, probe_ttable
from nemo.core.transposition import TTable, Killers
from nemo.core.constants import STARTING_FEN, MAX_PLY
from nemo.core.utils import pairwise

logging.basicConfig(filename='nemo.log', level=logging.DEBUG)

T = TypeVar("T")

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
        # sys.stderr.write(data)
        # sys.stderr.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

def output(line: str) -> None:
    out = Unbuffered(sys.stdout)
    print(line, file=out)
    logging.debug(line)


class Timer:
    def __init__(self, timeout: float, callback: Callable[..., Any]):
        self.__timeout = timeout
        self.__callback = callback
        self.__task = asyncio.create_task(self.__job())

    async def __job(self):
        await asyncio.sleep(self.__timeout)
        await self.__callback()

    def cancel(self):
        self.__task.cancel()


class UCIParser:
    @classmethod
    def parse(line: str):
        pass


class AbstractUCIInterface(ABC):
    @abstractmethod
    async def uci(self):
        raise NotImplementedError()

    @abstractmethod
    async def debug(self, on):
        raise NotImplementedError()

    @abstractmethod
    async def isready(self):
        raise NotImplementedError()

    @abstractmethod
    async def setoption(self, options):
        raise NotImplementedError()

    @abstractmethod
    async def ucinewgame(self, on: str):
        raise NotImplementedError()

    @abstractmethod
    async def position(self, board: str):
        raise NotImplementedError()

    @abstractmethod
    async def go(self, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    async def stop(self):
        raise NotImplementedError()

    @abstractmethod
    async def ponderhit(self):
        raise NotImplementedError()

    @abstractmethod
    async def quit(self):
        raise NotImplementedError()



class Engine(AbstractUCIInterface):

    def __init__(self, executor: ThreadPoolExecutor = None):
        self.__debug = False
        self.__options = {}
        self.__position = Position()
        self.__fen = STARTING_FEN
        self.__key = self.__position.key

        self.__executor = executor or ThreadPoolExecutor(max_workers=4)
        self.__stopped = Event()
        self.__searcher = Searcher(event=self.__stopped)
        self.__search_task = None
        self.__tasks = deque([])
        self.__best_move = None

        self.__ponder = False
        self.__timeout = None
        self.__depth = None

    async def _wait(self, *args, timeout: float = None):
        future = self.__executor.submit(*args)
        self.__futures.appendleft(future)
        try:
            result = future.result(timeout=timeout)
        except TimeoutError:
            result = probe_ttable(self.__key)
        if result is not None:
            self.__best_move = str(result.move)
        output(f"bestmove {self.__best_move}")

    async def uci(self) -> None:
        output("id name nemo")
        output("id author @rainmayecho")
        output("uciok")

    async def debug(self, on) -> None:
        self.__debug = on == "on"

    async def isready(self):
        output("readyok")

    async def setoption(self, options) -> None:
        pass

    async def ucinewgame(self):
        await self.stop()
        self.__position = Position()

    async def position(
        self, fen: str = None, moves: List[str] = None
    ) -> None:
        if fen == "startpos":
            fen = STARTING_FEN
        p = Position(fen=fen)
        if moves is not None:
            moves = moves.split(" ")
            for move in moves:
                p.make_move(Move(uci=move))
        self.__position = p
        self.__key = p.key
        self.__fen = fen

    async def go(self,
        searchmoves: str = None,
        ponder: bool = None,
        wtime: int = None,
        btime: int = None,
        winc: int = None,
        binc: int = None,
        movestogo: int = None,
        depth: int = None,
        mate: int = None,
        movetime: int = None,
        infinite: bool = None,
    ):
        self.__best_move = None
        if ponder is not None:
            self.__ponder = ponder

        if depth is not None:
            self.__depth = depth
        else:
            self.__depth = 12

        self.__search_task = self.__executor.submit(
            self.__searcher.search, self.__position, self.__depth
        )
        if movetime is not None:
            self.__timeout = movetime / 1000
            Timer(self.__timeout, self.stop)

    async def stop(self):
        self.__stopped.set()
        self.bestmove()
        self.reset()

    def reset(self):
        self.__position = Position(fen=self.__fen)
        self.__stopped.clear()

    async def ponderhit(self):
        pass

    async def info(self):
        pv = f"Principal Variation: {' '.join(s for s in self.iter_formatted_principal_variation())}"
        output(pv)
        pprint(self.__searcher.stats)

    async def quit(self):
        sys.exit(0)

    def iter_formatted_principal_variation(self, uci=True):
        it = iter(TTable.extract_principal_variation(Position(fen=self.__fen)))
        getter = (lambda e: e[2]) if not uci else (lambda e: str(e[0]))
        for i, nodes in enumerate(pairwise(it)):
            first, second = nodes
            san_str = getter(first)
            if second is None:
                yield f"{i + 1}. {san_str} "
            else:
                second_san_str = getter(second)
                yield f"{i + 1}. {san_str} {second_san_str}"
    @property
    def searchtask(self):
        return self.__search_task

    def bestmove(self) -> None:
        if self.__best_move is None:
            self.__best_move = probe_ttable(self.key).move
        output(f"bestmove {self.__best_move}")

    @property
    def key(self):
        return self.__key


async def ainput(prompt: str = "", executor = None):
    return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)

async def main():
    executor = ThreadPoolExecutor()
    engine = Engine(executor=executor)
    loop = asyncio.get_running_loop()

    task = None
    while True:
        inp = (await ainput("", executor=executor)).split(" ")
        cmd, args = None, tuple()
        if len(inp) >= 2:
            cmd, args = inp[0], (" ".join(inp[1:]),)
        else:
            cmd = inp[0]
        try:
            await asyncio.create_task(getattr(engine, cmd)(*args))
        except AttributeError as e:
            print(e)


if __name__ == "__main__":
    asyncio.run(main())
    """
    1. a4 a5 2. Nc3 b5 3. axb5 b8a6 is problematic
    """