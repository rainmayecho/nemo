import berserk
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
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
THINK_TIME = 20

_session = None
_client = None
executor = ThreadPoolExecutor()

def get_session():
    global _session
    if _session is None:
        _session = berserk.TokenSession(TOKEN)
    return _session

def get_client(session):
    global _client
    if _client is None:
        _client = berserk.Client(session)
    return _client

def gamefull(position, state):
    pass

def gamestate(position, state):
    pass


funcmap = {
    "gamestate": gamestate,
    "gamefull": gamefull,
    "default": lambda state: None
}

def interrupt(wait_time, event):
    print(f"thinking for {wait_time} seconds")
    sleep(wait_time)
    if event is not None:
        event.set()
        print(f"taking too long! interrupting.")

def think(searcher, position, depth=6, event=None):
    if event.is_set():
        event.clear()

    p = deepcopy(position)
    print(position.key, p.key)
    print(position.fen, p.fen)
    tasks = [
        executor.submit(searcher.search, p, depth),
        executor.submit(interrupt, THINK_TIME, event),
    ]
    wait(tasks, timeout=20, return_when=FIRST_COMPLETED)
    print("done thinking")
    result = probe_ttable(position.key)
    print(position.key, TTable.get(position.key))
    if result is not None:
        return result.move
    return None

def main():
    session = get_session()
    lichess = get_client(session)
    self_color = None
    position = None
    stopping_event = Event()
    searcher = Searcher(event=stopping_event)
    game_id = None

    def make_move(move):
        nonlocal game_id
        if move is not None:
            position.make_move(move, uci=True)
            lichess.bots.make_move(game_id, move.uci)

    for event in lichess.bots.stream_incoming_events():
        print(event)
        if event["type"] == "challenge":
            challenge = event["challenge"]
            if challenge["variant"]["key"] == "standard":
                if not challenge["rated"]:
                    game_id = challenge["id"]
                    lichess.bots.accept_challenge(game_id)
        elif event["type"] == "gameStart":
            game_id = event["game"]["id"]
        # else:
        #     game_id = event["game"]["id"]
        #     challenge = {"color": "random"}
        if game_id is not None:
            for game_state in lichess.bots.stream_game_state(game_id):
                if self_color is None and "white" in game_state:
                    self_color = Color(1 - int(game_state["white"]["id"] == BOT_ID))
                    print(f"Playing as {self_color}")

                _type = game_state["type"]
                print(game_state)
                if _type == "gameFull":
                    if game_state["state"]["moves"] == "":
                        if game_state["initialFen"] == "startpos":
                            position = Position()
                        else:
                            position = Position(fen=game_state["initialFen"])
                    else:
                        position = Position()
                        for uci in game_state["state"]["moves"].split(" "):
                            position.make_move(Move(uci=uci), uci=True)

                    moves = game_state["state"]["moves"].split(" ")
                    white_to_play = not (len(moves) % 2)
                    if (
                        white_to_play and self_color is Color.WHITE or
                        not white_to_play and self_color is Color.BLACK
                    ):
                        move = think(searcher, position, event=stopping_event)
                        make_move(move)

                elif _type == "gameState":
                    moves = game_state["moves"].split(" ")
                    white_to_play = not (len(moves) % 2)
                    print(white_to_play, self_color)
                    if (
                        white_to_play and self_color is Color.WHITE or
                        not white_to_play and self_color is Color.BLACK
                    ):
                        position.make_move(Move(uci=moves[-1]), uci=True)
                        move = think(searcher, position, event=stopping_event)
                        make_move(move)





if __name__ == "__main__":
    main()