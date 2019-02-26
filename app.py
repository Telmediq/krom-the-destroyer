import random
import asyncio

from collections import defaultdict
from aiohttp import web
from libsnek import data, movement


COLOR = "#cc4343"
HEAD_TYPES = ["smile", "tongue"]
TAIL_TYPES = ["fat-rattle", "small-rattle"]


routes = web.RouteTableDef()


def pos_to_move(board_state, pos):
    moves = zip(
        movement.surroundings(board_state.you.head),
        ["up", "right", "down", "left"]
    )

    for p, d in moves:
        if pos == p:
            return d

    return "up"


def get_move(board_state):

    my_pos = board_state.you.head

    # First, try to head towards the target snake
    target_snake = get_target_snake(board_state)

    if target_snake is not None:
        print("Target snake", target_snake.head)

        minlen = 100
        best_move = None
        for pos in movement.surroundings(target_snake.head):

            if not movement.is_ok(board_state, pos):
                continue

            path = movement.find_path(board_state, my_pos, pos)
            if path is None or len(path) == 0:
                continue

            if best_move is None or len(path) < minlen:
                minlen = len(path)
                best_move = path[0]

        if best_move is not None:
            return pos_to_move(board_state, best_move)


    # Second, head in a safe direction

    safe_options = [
        pos for pos in movement.surroundings(my_pos)
        if movement.is_safe(board_state, pos)
    ]

    if safe_options:
        print("Moving to safe options", safe_options)
        return pos_to_move(board_state, random.choice(safe_options))

    # Third, head in an acceptable direction

    ok_options = [
        pos for pos in movement.surroundings(my_pos)
        if movement.is_ok(board_state, pos)
    ]

    if ok_options:
        print("Moving to ok options", ok_options)
        return pos_to_move(board_state, random.choice(ok_options))

    return "up"


OWN_SNAKES_LOCK = asyncio.Lock()
OWN_SNAKES_BY_GAME = defaultdict(set)


async def register_own_snake(board):
    async with OWN_SNAKES_LOCK:
        OWN_SNAKES_BY_GAME[board.id].add(board.you.id)


def get_target_snake(board_state):
    game_id = board_state.id
    own_snake_ids = OWN_SNAKES_BY_GAME[game_id]
    for s in board_state.other_snakes:
        if s.id not in own_snake_ids:
            return s

    return None


@routes.post('/start')
async def start(request):
    board = data.BoardState(await request.json())
    await register_own_snake(board)

    return web.json_response({
        "color": COLOR,
        "headType": random.choice(HEAD_TYPES),
        "tailType": random.choice(TAIL_TYPES),
    })


@routes.post('/move')
async def move(request):
    board = data.BoardState(await request.json())

    print(f"--- Turn {board.turn} ---")
    return web.json_response({"move": get_move(board)})


@routes.post("/end")
async def end(request):
    return web.Response()


@routes.post("/ping")
async def ping(request):
    return web.Response()


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=7001)

