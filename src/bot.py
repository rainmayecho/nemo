import berserk
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from threading import Event
from time import sleep
from copy import deepcopy

from nemo.core.game import Game
from nemo.core.move import Move
from nemo.core.position import Position
from nemo.core.search import Searcher, probe_ttable
from nemo.core.transposition import TTable, Killers
from nemo.core.constants import STARTING_FEN, MAX_PLY
from nemo.core.types import Color

TOKEN = "rKNO7FtOKmHf6up1"
BOT_ID = "anemone-nemisis"
THINK_TIME = 3

_session = None
_client = None
executor = ThreadPoolExecutor()
process_pool = ProcessPoolExecutor()

def get_session():
    global _session
    if _session is None:
        _session = berserk.TokenSession(TOKEN)
    return _session

def get_client(session=None):
    session = session or get_session()
    global _client
    if _client is None:
        _client = berserk.Client(get_session())
    return _client

def interrupt(wait_time, event):
    print(f"thinking for {wait_time} seconds")
    sleep(wait_time)
    if event is not None:
        event.set()
        print(f"taking too long! interrupting.")

def think(searcher, position, time: float = THINK_TIME, depth=7, event=None):
    if event.is_set():
        event.clear()

    p = deepcopy(position)
    tasks = [
        executor.submit(searcher.search, p, depth),
        executor.submit(interrupt, time, event),
    ]
    wait(tasks, timeout=time + 1, return_when=FIRST_COMPLETED)
    print("done thinking")
    result = probe_ttable(position.key)
    print(position)
    if result is not None:
        return result.move
    return None

class TimeManager:
    @staticmethod
    def estimate_time_to_think(position, remaining, increment):
        n = position.state.ply
        print(f"ply = {n}")
        if n < 40:
            t = (.85 * remaining) / 40
        else:
            t = max(increment - .5, 1)
        print(f"Take {t} seconds to think.")
        return t

@dataclass
class TimeControl:
    initial: float = 180
    increment: float = 2

class Game:
    time_manager = TimeManager

    def __init__(self, _id : str = None, color: Color = None, executor = None):
        self.__client = get_client(get_session())
        self.__id = _id
        self.__event = Event()
        self.__searcher = Searcher(event=self.__event)
        self.__color = color
        self.__position = Position()
        self.__time_control = None
        self.__time_remaining = None
        self.__proxy_move_partial = partial(self.__client.bots.make_move, self.__id)
        self.__game_over = False
        self.think = partial(think, self.__searcher, event=self.__event)
        self.run()

    def iterstates(self) -> "Generator[Position, None, None]":
        while not self.__game_over:
            for game_state in self.__client.bots.stream_game_state(self.__id):
                print(game_state)
                if self.color is None and "white" in game_state:
                    self.color = Color(1 - int(game_state["white"].get("id") == BOT_ID))
                    print(f"Playing as {self.color}")
                if self.__time_control is None and "clock" in game_state:
                    clock = game_state["clock"]
                    self.__time_control = TimeControl(
                        initial=clock["initial"]  / 1000, increment=clock["increment"] / 1000
                    )
                    self.__time_remaining = clock["initial"]  / 1000

                _type = game_state["type"]
                if _type == "gameFull":
                    if game_state["state"]["moves"] == "":
                        if game_state["initialFen"] == "startpos":
                            self.__position = Position()
                        else:
                            self.__position = Position(fen=game_state["initialFen"])
                    else:
                        self.__position = Position()
                        for uci in game_state["state"]["moves"].split(" "):
                            self.__position.make_move(Move(uci=uci), uci=True)
                elif _type == "gameState":
                    moves = game_state["moves"].split(" ")
                    self.__position = Position()
                    for uci in moves:
                        self.__position.make_move(Move(uci=uci), uci=True)
                elif _type == "gameFinish":
                    self.__game_over = True
                    break


                self.__set_time_remaining(game_state)
                yield (
                    self.__position,
                    self.__time_remaining,
                    self.__time_control.increment,
                    self.__position.state.turn == self.__color
                )

    def __set_time_remaining(self, game_state) -> None:
        key = "wtime" if self.__color == Color.WHITE else "btime"
        t = None
        if key in game_state:
            t = game_state[key]
        elif key in game_state.get("state", {}):
            t = game_state["state"][key]
        if isinstance(t, (float, int)):
            t /= 1000
        elif isinstance(t, datetime):
            t = t.minute * 60 + t.second
        self.__time_remaining = t


    def is_own_turn(self):
        return self.__position.state.turn == self.__color

    @property
    def color(self) -> Color:
        return self.__color

    @color.setter
    def color(self, value: Color) -> None:
        self.__color = value


    def run(self):
        try:
            for position, time_remaining, increment, play in self.iterstates():
                if play:
                    think_time = TimeManager.estimate_time_to_think(position, time_remaining, increment)
                    move = self.think(position, time=think_time)
                    self.make_move(move)
        except Exception as e:
            print(e)


    def make_move(self, move):
        if move is not None:
            self.__position.make_move(move, uci=True)
            self.__proxy_move_partial(move.uci)

active_games = {}

def launch_game(game_id) -> None:
    global active_games
    future = executor.submit(Game, _id=game_id)
    active_games[game_id] = future

def main():
    session = get_session()
    lichess = get_client(session)
    global active_games

    # _created_challenge = lichess.challenges.create_open(clock_limit=180, clock_increment=2)
    # print(_created_challenge)
    # lichess.bots.accept_challenge(_created_challenge["challenge"]["id"])
    for event in lichess.bots.stream_incoming_events():
        print(event)
        if event["type"] == "challenge":
            challenge = event["challenge"]
            if challenge["variant"]["key"] == "standard":
                game_id = challenge["id"]
                if game_id not in active_games:
                    lichess.bots.accept_challenge(game_id)
                    launch_game(game_id)
                    print(active_games)

        elif event["type"] == "gameStart":
            game_id = event["game"]["id"]
            if game_id not in active_games:
                launch_game(game_id)
                print(active_games)
        else:
            print(active_games)

if __name__ == "__main__":
    main()