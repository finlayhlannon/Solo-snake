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
        "color": "#12A434",
        "head": "lantern-fish",
        "tail": "do-sammy",
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

    visited = [[False] * game_state['board']['height'] for _ in range(game_state['board']['width']]]
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

# Constants for easy value adjustment
BOARDER_PENALTY = 1000
NEAR_BOARDER_PENALTY = 2
BODY_PENALTY = 100
OPPONENT_PENALTY = 100
FOOD_REWARD = 10
TRAP_PENALTY = 2
TRAP_REWARD = 2
FLOOD_FILL_ADJUSTMENT = 10

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
    opponents = [snake['body'] for snake in game_state['board']['snakes']]

    my_body_length = len(my_body)

    # Avoid moving back on the neck
    if my_neck["x"] < my_head["x"]:
        lvalue -= BOARDER_PENALTY
    elif my_neck["x"] > my_head["x"]:
        rvalue -= BOARDER_PENALTY
    elif my_neck["y"] < my_head["y"]:
        dvalue -= BOARDER_PENALTY
    elif my_neck["y"] > my_head["y"]:
        uvalue -= BOARDER_PENALTY

    # Avoid walls
    if my_head["x"] <= 0:
        lvalue -= BOARDER_PENALTY
    if my_head["x"] >= board_width - 1:
        rvalue -= BOARDER_PENALTY
    if my_head["y"] <= 0:
        dvalue -= BOARDER_PENALTY
    if my_head["y"] >= board_height - 1:
        uvalue -= BOARDER_PENALTY

    # Avoid near walls
    if my_head["x"] <= 1:
        lvalue -= NEAR_BOARDER_PENALTY
    if my_head["x"] >= board_width - 2:
        rvalue -= NEAR_BOARDER_PENALTY
    if my_head["y"] <= 1:
        dvalue -= NEAR_BOARDER_PENALTY
    if my_head["y"] >= board_height - 2:
        uvalue -= NEAR_BOARDER_PENALTY

    # Avoid self collision
    if {'x': my_head["x"] + 1, 'y': my_head["y"]} in my_body:
        rvalue -= BODY_PENALTY
    if {'x': my_head["x"] - 1, 'y': my_head["y"]} in my_body:
        lvalue -= BODY_PENALTY
    if {'x': my_head['x'], 'y': my_head["y"] - 1} in my_body:
        dvalue -= BODY_PENALTY
    if {'x': my_head['x'], 'y': my_head["y"] + 1} in my_body:
        uvalue -= BODY_PENALTY
        
    # Avoid opponent collision
    for i in range(1, len(opponents)):
        if {'x': my_head["x"] + 1, 'y': my_head["y"]} in opponents[i]:
            rvalue -= OPPONENT_PENALTY
        if {'x': my_head["x"] - 1, 'y': my_head["y"]} in opponents[i]:
            lvalue -= OPPONENT_PENALTY
        if {'x': my_head['x'], 'y': my_head["y"] - 1} in opponents[i]:
            dvalue -= OPPONENT_PENALTY
        if {'x': my_head['x'], 'y': my_head["y"] + 1} in opponents[i]:
            uvalue -= OPPONENT_PENALTY

        # Head-on collision check
        if my_body_length <= len(opponents[i]):
            if {'x': my_head["x"] + 2, 'y': my_head["y"]} == opponents[i][0]:
                rvalue -= OPPONENT_PENALTY
            if {'x': my_head["x"] - 2, 'y': my_head["y"]} == opponents[i][0]:
                lvalue -= OPPONENT_PENALTY
            if {'x': my_head['x'], 'y': my_head["y"] - 2} == opponents[i][0]:
                dvalue -= OPPONENT_PENALTY
            if {'x': my_head['x'], 'y': my_head["y"] + 2} == opponents[i][0]:
                uvalue -= OPPONENT_PENALTY

    # Move towards food
    if len(food) > 0:
        path = bfs_shortest_path(game_state, my_head, food)
        if len(path) > 0:
            next_move = path[1]
            if next_move['x'] > my_head['x']:
                rvalue += FOOD_REWARD
            if next_move['x'] < my_head['x']:
                lvalue += FOOD_REWARD
            if next_move['y'] > my_head['y']:
                uvalue += FOOD_REWARD
            if next_move['y'] < my_head['y']:
                dvalue += FOOD_REWARD

    # Flood fill area evaluation
    flood_fill_area = get_flood_fill_area(game_state, my_head)
    print(f"Flood fill area: {flood_fill_area}")
    
    if flood_fill_area < 5:
        if health < 50:
            trap_reward = TRAP_REWARD if flood_fill_area >= 2 else -TRAP_REWARD
            rvalue += trap_reward
            lvalue += trap_reward
            uvalue += trap_reward
            dvalue += trap_reward
        else:
            trap_penalty = TRAP_PENALTY if flood_fill_area < 2 else -TRAP_PENALTY
            rvalue -= trap_penalty
            lvalue -= trap_penalty
            uvalue -= trap_penalty
            dvalue -= trap_penalty
    else:
        flood_fill_reward = flood_fill_area // FLOOD_FILL_ADJUSTMENT
        rvalue += flood_fill_reward
        lvalue += flood_fill_reward
        uvalue += flood_fill_reward
        dvalue += flood_fill_reward

    # Determine move
    direction_values = {"up": uvalue, "down": dvalue, "left": lvalue, "right": rvalue}
    move = max(direction_values, key=direction_values.get)
    print(f"Move values: Right: {rvalue} Left: {lvalue} Up: {uvalue} Down: {dvalue}")
    print(f"Move: {move}")

    return {"move": move}

if __name__ == "__main__":
    app.run(host=host, port=port, debug=True)
