import logging
import os
import typing
from flask import Flask, request, jsonify
from collections import deque

app = Flask(__name__)

@app.get("/")
def on_info():
    return info()

@app.post("/start")
def on_start():
    print("go!")
    game_state = request.get_json()
    start(game_state)
    return "ok"

@app.post("/move")
def on_move():
    game_state = request.get_json()
    return move(game_state)

@app.post("/end")
def on_end():
    game_state = request.get_json()
    end(game_state)
    return "ok"

@app.after_request
def identify_server(response):
    response.headers.set("server", "battlesnake/github/starter-snake-python")
    return response

@app.errorhandler(500)
def internal_error(error):
    response = jsonify({"message": "Internal server error", "error": str(error)})
    response.status_code = 500
    return response

host = "0.0.0.0"
port = int(os.environ.get("PORT", "8000"))
logging.getLogger("werkzeug").setLevel(logging.ERROR)
print(f"\nRunning Battlesnake at http://{host}:{port}")

import random
import typing

def info() -> typing.Dict:
    print("INFO")
    return {
        "apiversion": "1",
        "author": "Finlay",
        "color": "#12A483",
        "head": "silly",
        "tail": "curled",
    }

def start(game_state: typing.Dict):
    global start_snake_count
    start_snake_count = len(game_state['board']['snakes'])
    print("GAME START with ", start_snake_count, " snakes")

def end(game_state: typing.Dict):
    print("GAME OVER!    Right:", rvalue, " Left:", lvalue, " Up:", uvalue, " Down:", dvalue)

def flood_fill(board, x, y, visited):
    if x < 0 or y < 0 or x >= len(board) or y >= len(board[0]) or board[x][y] == 1 or visited[x][y]:
        return 0
    visited[x][y] = True
    return 1 + flood_fill(board, x + 1, y, visited) + flood_fill(board, x - 1, y, visited) + flood_fill(board, x, y + 1, visited) + flood_fill(board, x, y - 1, visited)

def get_flood_fill_area(game_state, head):
    board = [[0] * game_state['board']['height'] for _ in range(game_state['board']['width'])]

    # Mark all opponent snakes' segments as occupied
    for snake in game_state['board']['snakes']:
        for segment in snake['body']:
            board[segment['x']][segment['y']] = 1

    # Mark your own snake's segments as occupied, except for the tail
    for i, segment in enumerate(game_state['you']['body'][:-5]):
        board[segment['x']][segment['y']] = 1

    visited = [[False] * game_state['board']['height'] for _ in range(game_state['board']['width'])]
    return flood_fill(board, head['x'], head['y'], visited)

def bfs_shortest_path(game_state, start, food):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    queue = deque([start])
    visited = set()
    visited.add((start['x'], start['y']))
    parent = {(start['x'], start['y']): None}

    while queue:
        current = queue.popleft()
        if (current['x'], current['y']) in food:
            path = []
            while current:
                path.append(current)
                current = parent[(current['x'], current['y'])]
            path.reverse()
            return path

        for direction in directions:
            neighbor = {'x': current['x'] + direction[0], 'y': current['y'] + direction[1]}
            if 0 <= neighbor['x'] < game_state['board']['width'] and 0 <= neighbor['y'] < game_state['board']['height']:
                if (neighbor['x'], neighbor['y']) not in visited:
                    if neighbor not in game_state['you']['body'] and all(neighbor not in snake['body'] for snake in game_state['board']['snakes']):
                        queue.append(neighbor)
                        visited.add((neighbor['x'], neighbor['y']))
                        parent[(neighbor['x'], neighbor['y'])] = current
    return []


def move(game_state: typing.Dict) -> typing.Dict:
    global rvalue, lvalue, uvalue, dvalue
    rvalue, lvalue, uvalue, dvalue = 0, 0, 0, 0
    my_head = game_state["you"]["body"][0]
    my_neck = game_state["you"]["body"][1]
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    health = game_state['you']['health']
    my_body = game_state['you']['body']
    my_tail = my_body[-1]
    food = game_state['board']['food']
    #print(opponents[start_snake_count - 1][0])
    #print(my_body[0])

    my_body_length = len(game_state["you"]["body"])

    if my_neck["x"] < my_head["x"]:
        lvalue = -100
    elif my_neck["x"] > my_head["x"]:
        rvalue = -100
    elif my_neck["y"] < my_head["y"]:
        dvalue = -100
    elif my_neck["y"] > my_head["y"]:
        uvalue = -100

    if my_head["x"] <= 0:
        lvalue -= 100
    if my_head["x"] >= board_width - 1:
        rvalue -= 100
    if my_head["y"] <= 0:
        dvalue -= 100
    if my_head["y"] >= board_height - 1:
        uvalue -= 100

    if my_head["x"] <= 1:
        lvalue -= 2
    if my_head["x"] >= board_width - 2:
        rvalue -= 2
    if my_head["y"] <= 1:
        dvalue -= 2
    if my_head["y"] >= board_height - 2:
        uvalue -= 2

    if {'x': my_head["x"] + 1, 'y': my_head["y"]} in my_body:
        rvalue -= 100
    if {'x': my_head["x"] - 1, 'y': my_head["y"]} in my_body:
        lvalue -= 100
    if {'x': my_head['x'], 'y': my_head["y"] - 1} in my_body:
        dvalue -= 100
    if {'x': my_head['x'], 'y': my_head["y"] + 1} in my_body:
        uvalue -= 100
        
    #trapping myself
    if {'x': my_head["x"] + 2, 'y': my_head["y"]} in my_body:
        if {
                'x': my_head["x"] + 2,
                'y': my_head["y"]
        } == my_tail and health <= 99:
            rvalue += 2
        else:
            rvalue -= 2
    if {'x': my_head["x"] - 2, 'y': my_head["y"]} in my_body:
        if {
                'x': my_head["x"] - 2,
                'y': my_head["y"]
        } == my_tail and health <= 99:
            lvalue += 2
        else:
            lvalue -= 2
    if {'x': my_head['x'], 'y': my_head["y"] - 2} in my_body:
        if {
                'x': my_head['x'],
                'y': my_head["y"] - 2
        } == my_tail and health <= 99:
            dvalue += 2
        else:
            dvalue -= 2
    if {'x': my_head['x'], 'y': my_head["y"] + 2} in my_body:
        if {
                'x': my_head['x'],
                'y': my_head["y"] + 2
        } == my_tail and health <= 99:
            uvalue += 2
        else:
            uvalue -= 2

    if {'x': my_head["x"] + 1, 'y': my_head["y"] + 1} in my_body:
        if {
                'x': my_head["x"] + 1,
                'y': my_head["y"] + 1
        } == my_tail and health <= 99:
            rvalue += 2
        else:
            rvalue -= 2
    if {'x': my_head["x"] - 1, 'y': my_head["y"] - 1} in my_body:
        if {
                'x': my_head["x"] - 1,
                'y': my_head["y"] - 1
        } == my_tail and health <= 99:
            lvalue += 2
        else:
            lvalue -= 2
    if {'x': my_head['x'] - 1, 'y': my_head["y"] - 1} in my_body:
        if {
                'x': my_head['x'] - 1,
                'y': my_head["y"] - 1
        } == my_tail and health <= 99:
            dvalue += 2
        else:
            dvalue -= 2
    if {'x': my_head['x'] + 1, 'y': my_head["y"] + 1} in my_body:
        if {
                'x': my_head['x'] + 1,
                'y': my_head["y"] + 1
        } == my_tail and health <= 99:
            uvalue += 2
        else:
            uvalue -= 2

    if {'x': my_head["x"] + 1, 'y': my_head["y"] - 1} in my_body:
        if {
                'x': my_head["x"] + 1,
                'y': my_head["y"] - 1
        } == my_tail and health <= 99:
            rvalue += 2
        else:
            rvalue -= 2
    if {'x': my_head["x"] - 1, 'y': my_head["y"] + 1} in my_body:
        if {
                'x': my_head["x"] - 1,
                'y': my_head["y"] + 1
        } == my_tail and health <= 99:
            lvalue += 2
        else:
            lvalue -= 2

    # BFS for food
    nearest_food_path = bfs_shortest_path(game_state, my_head, set((f['x'], f['y']) for f in food))
    if nearest_food_path and len(nearest_food_path) > 1:
        next_move = nearest_food_path[1]
        if health <= 10:
            if next_move['x'] > my_head['x']:
                rvalue += 10
            elif next_move['x'] < my_head['x']:
                lvalue += 10
            elif next_move['y'] > my_head['y']:
                uvalue += 10
            elif next_move['y'] < my_head['y']:
                dvalue += 10
        else:
            if next_move['x'] > my_head['x']:
                rvalue -= 10
            elif next_move['x'] < my_head['x']:
                lvalue -= 10
            elif next_move['y'] > my_head['y']:
                uvalue -= 10
            elif next_move['y'] < my_head['y']:
                dvalue -= 10

    flood_fill_area = {
        "up":
        get_flood_fill_area(game_state, {
            "x": my_head["x"],
            "y": my_head["y"] + 1
        }),
        "down":
        get_flood_fill_area(game_state, {
            "x": my_head["x"],
            "y": my_head["y"] - 1
        }),
        "left":
        get_flood_fill_area(game_state, {
            "x": my_head["x"] - 1,
            "y": my_head["y"]
        }),
        "right":
        get_flood_fill_area(game_state, {
            "x": my_head["x"] + 1,
            "y": my_head["y"]
        })
    }

    # Determine max flood fill area
    max_area = max(flood_fill_area.values())
    min_area = min(flood_fill_area.values())

    for direction, area in flood_fill_area.items():
        if area == max_area and max_area != min_area:
            if direction == "right":
                rvalue += 20
            elif direction == "left":
                lvalue += 20
            elif direction == "up":
                uvalue += 20
            elif direction == "down":
                dvalue += 20
        elif area == min_area and max_area != min_area:
            if direction == "right":
                rvalue -= 20
            elif direction == "left":
                lvalue -= 20
            elif direction == "up":
                uvalue -= 20
            elif direction == "down":
                dvalue -= 20
        else:
            rvalue += 0
            lvalue += 0
            uvalue += 0
            dvalue += 0

    max_value = max(rvalue, lvalue, uvalue, dvalue)

    if rvalue == max_value:
        move = "right"
        print(rvalue)
    elif lvalue == max_value:
        move = "left"
        print(lvalue)
    elif uvalue == max_value:
        move = "up"
        print(uvalue)
    else:
        move = "down"
        print(dvalue)


    return {"move": move}

if __name__ == "__main__":
    handlers = {"info": info, "start": start, "move": move, "end": end}
    run_server(handlers)
