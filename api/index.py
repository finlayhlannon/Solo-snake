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

# Variable definitions
border_penalty = 1000
close_border_penalty = 2
body_collision_penalty = 100
head_on_collision_penalty = 100
corner_collision_penalty = 100
trapping_penalty = 2
food_value = 10
flood_fill_bonus = 20
wall_penalty = 10

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
    opponents = [snake['body'] for snake in game_state['board']['snakes']]

    # Check direction based on neck and head positions
    if my_neck["x"] < my_head["x"]:
        lvalue -= body_collision_penalty
    elif my_neck["x"] > my_head["x"]:
        rvalue -= body_collision_penalty
    elif my_neck["y"] < my_head["y"]:
        dvalue -= body_collision_penalty
    elif my_neck["y"] > my_head["y"]:
        uvalue -= body_collision_penalty

    # Border penalties
    if my_head["x"] <= 0:
        lvalue -= border_penalty
    if my_head["x"] >= board_width - 1:
        rvalue -= border_penalty
    if my_head["y"] <= 0:
        dvalue -= border_penalty
    if my_head["y"] >= board_height - 1:
        uvalue -= border_penalty

    if my_head["x"] <= 1:
        lvalue -= close_border_penalty
    if my_head["x"] >= board_width - 2:
        rvalue -= close_border_penalty
    if my_head["y"] <= 1:
        dvalue -= close_border_penalty
    if my_head["y"] >= board_height - 2:
        uvalue -= close_border_penalty

    # Body collision penalties
    if {'x': my_head["x"] + 1, 'y': my_head["y"]} in my_body:
        rvalue -= body_collision_penalty
    if {'x': my_head["x"] - 1, 'y': my_head["y"]} in my_body:
        lvalue -= body_collision_penalty
    if {'x': my_head['x'], 'y': my_head["y"] - 1} in my_body:
        dvalue -= body_collision_penalty
    if {'x': my_head['x'], 'y': my_head["y"] + 1} in my_body:
        uvalue -= body_collision_penalty
        
    # Opponent collision penalties
    if start_snake_count >= 2:
        if {'x': my_head["x"] + 1, 'y': my_head["y"]} in opponents[1]:
            rvalue -= body_collision_penalty
        if {'x': my_head["x"] - 1, 'y': my_head["y"]} in opponents[1]:
            lvalue -= body_collision_penalty
        if {'x': my_head['x'], 'y': my_head["y"] - 1} in opponents[1]:
            dvalue -= body_collision_penalty
        if {'x': my_head['x'], 'y': my_head["y"] + 1} in opponents[1]:
            uvalue -= body_collision_penalty
    else:
        pass

    # Head-on collision penalties
    if start_snake_count == 1:
        pass
    elif start_snake_count >= 2 and len(opponents) > 1:
        opponent1_length = len(opponents[1])

        if {'x': my_head["x"] + 2, 'y': my_head["y"]} == opponents[1][0]:
            if len(my_body) <= opponent1_length:
                rvalue -= head_on_collision_penalty
            else:
                rvalue += head_on_collision_penalty
        if {'x': my_head["x"] - 2, 'y': my_head["y"]} == opponents[1][0]:
            if len(my_body) <= opponent1_length:
                lvalue -= head_on_collision_penalty
            else:
                lvalue += head_on_collision_penalty
        if {'x': my_head["x"], 'y': my_head["y"] - 2} == opponents[1][0]:
            if len(my_body) <= opponent1_length:
                dvalue -= head_on_collision_penalty
            else:
                dvalue += head_on_collision_penalty
        if {'x': my_head["x"], 'y': my_head["y"] + 2} == opponents[1][0]:
            if len(my_body) <= opponent1_length:
                uvalue -= head_on_collision_penalty
            else:
                uvalue += head_on_collision_penalty

    # Food bonuses
    for food_item in food:
        path = bfs_shortest_path(game_state, my_head, [food_item])
        if path:
            distance = len(path)
            if food_item['x'] > my_head['x']:
                rvalue += food_value / distance
            if food_item['x'] < my_head['x']:
                lvalue += food_value / distance
            if food_item['y'] > my_head['y']:
                uvalue += food_value / distance
            if food_item['y'] < my_head['y']:
                dvalue += food_value / distance
    
    # Flood fill bonuses
    flood_fill_area = get_flood_fill_area(game_state, my_head)
    if flood_fill_area:
        flood_fill_score = flood_fill_area * flood_fill_bonus
        rvalue += flood_fill_score
        lvalue += flood_fill_score
        uvalue += flood_fill_score
        dvalue += flood_fill_score

    # Select move with the highest value
    max_value = max(rvalue, lvalue, uvalue, dvalue)
    if max_value == rvalue:
        move = "right"
    elif max_value == lvalue:
        move = "left"
    elif max_value == uvalue:
        move = "up"
    elif max_value == dvalue:
        move = "down"
    else:
        move = "right"

    print(f"Move: {move}, Values: Right: {rvalue}, Left: {lvalue}, Up: {uvalue}, Down: {dvalue}")

    return {"move": move}

if __name__ == "__main__":
    app.run(host=host, port=port)
