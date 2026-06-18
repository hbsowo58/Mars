from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import random
from math import sqrt

app = FastAPI()

class InitRequest(BaseModel):
    height: int
    width: int

class MoveRequest(BaseModel):
    direction: str

game_state = {
    "grid": [],
    "rover": {"y": 1, "x": 1},
    "fuel": 0,
    "visited": [],
    "has_duplicates": False,
    "total_walkable_cells": 0,
    "exploration_progress": 0,
    "is_exploration_complete": False,
    "is_exploration_failed": False,
    "reachable_cells": []
}

@app.get("/api/hello")
def hello_api():
    return {"message": "Hello World"}

@app.post("/api/init")
def init_map(request: InitRequest):
    height = request.height
    width = request.width

    grid = [[0 for _ in range(width)] for _ in range(height)]

    for i in range(height):
        for j in range(width):
            if i == 0 or i == height - 1 or j == 0 or j == width - 1:
                grid[i][j] = 1

    for i in range(1, height - 1):
        for j in range(1, width - 1):
            if random.random() < 0.3:
                grid[i][j] = 1
            else:
                grid[i][j] = 0

    grid[1][1] = 0

    reachable = find_reachable_cells(grid, [1, 1])
    total_walkable = len(reachable)

    game_state["grid"] = grid
    game_state["rover"] = {"y": 1, "x": 1}
    game_state["fuel"] = 0
    game_state["visited"] = [[1, 1]]
    game_state["has_duplicates"] = False
    game_state["total_walkable_cells"] = total_walkable
    game_state["exploration_progress"] = int((1 / max(1, total_walkable)) * 100)
    game_state["is_exploration_complete"] = False
    game_state["is_exploration_failed"] = False
    game_state["reachable_cells"] = reachable

    response = {
        "grid": grid,
        "rover": {"y": 1, "x": 1},
        "fuel": 0,
        "visited": [[1, 1]],
        "has_duplicates": False,
        "total_walkable_cells": total_walkable,
        "exploration_progress": game_state["exploration_progress"],
        "is_exploration_complete": False,
        "is_exploration_failed": False,
        "reachable_cells": reachable
    }
    return response

@app.get("/api/status")
def get_status():
    return {
        "grid": game_state["grid"],
        "rover": game_state["rover"],
        "fuel": game_state["fuel"],
        "visited": game_state["visited"],
        "has_duplicates": game_state["has_duplicates"],
        "total_walkable_cells": game_state["total_walkable_cells"],
        "visited_count": len(game_state["visited"]),
        "exploration_progress": game_state["exploration_progress"],
        "is_exploration_complete": game_state["is_exploration_complete"],
        "is_exploration_failed": game_state["is_exploration_failed"],
        "reachable_cells": game_state.get("reachable_cells", []),
        "message": "현재 상태"
    }

@app.post("/api/move")
def move_rover(request: MoveRequest):
    direction = request.direction
    y, x = game_state["rover"]["y"], game_state["rover"]["x"]
    grid = game_state["grid"]

    new_y, new_x = y, x

    if direction == "up":
        new_y -= 1
    elif direction == "down":
        new_y += 1
    elif direction == "left":
        new_x -= 1
    elif direction == "right":
        new_x += 1

    if grid[new_y][new_x] == 0:
        game_state["rover"]["y"] = new_y
        game_state["rover"]["x"] = new_x
        game_state["fuel"] = min(100, game_state["fuel"] + 1)

        cell_coord = [new_y, new_x]
        if cell_coord in game_state["visited"]:
            game_state["has_duplicates"] = True
        else:
            game_state["visited"].append(cell_coord)

        visited_count = len(game_state["visited"])
        total_walkable = game_state["total_walkable_cells"]
        game_state["exploration_progress"] = int((visited_count / max(1, total_walkable)) * 100)

        if visited_count >= total_walkable:
            game_state["is_exploration_complete"] = True

        if game_state["fuel"] >= 100:
            game_state["is_exploration_failed"] = True

        return {
            "success": True,
            "rover": game_state["rover"],
            "fuel": game_state["fuel"],
            "visited": game_state["visited"],
            "has_duplicates": game_state["has_duplicates"],
            "total_walkable_cells": total_walkable,
            "visited_count": visited_count,
            "exploration_progress": game_state["exploration_progress"],
            "is_exploration_complete": game_state["is_exploration_complete"],
            "is_exploration_failed": game_state["is_exploration_failed"],
            "reachable_cells": game_state.get("reachable_cells", []),
            "message": "이동 성공 ✅"
        }
    else:
        game_state["fuel"] = min(100, game_state["fuel"] + 10)

        if game_state["fuel"] >= 100:
            game_state["is_exploration_failed"] = True

        return {
            "success": False,
            "rover": game_state["rover"],
            "fuel": game_state["fuel"],
            "visited": game_state["visited"],
            "has_duplicates": game_state["has_duplicates"],
            "total_walkable_cells": game_state["total_walkable_cells"],
            "visited_count": len(game_state["visited"]),
            "exploration_progress": game_state["exploration_progress"],
            "is_exploration_complete": game_state["is_exploration_complete"],
            "is_exploration_failed": game_state["is_exploration_failed"],
            "reachable_cells": game_state.get("reachable_cells", []),
            "message": "충돌 경고 ⚠️"
        }

def find_walkable_cells(grid):
    walkable = []
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if grid[y][x] == 0:
                walkable.append([y, x])
    return walkable

def find_reachable_cells(grid, start):
    from collections import deque
    reachable = set()
    queue = deque([tuple(start)])
    reachable.add(tuple(start))

    while queue:
        y, x = queue.popleft()

        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
                if grid[ny][nx] == 0 and (ny, nx) not in reachable:
                    reachable.add((ny, nx))
                    queue.append((ny, nx))

    return [list(cell) for cell in reachable]

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def find_shortest_path(grid, start, end):
    from collections import deque
    if start == end:
        return [start]

    queue = deque([(start, [start])])
    visited = {tuple(start)}

    while queue:
        [y, x], path = queue.popleft()

        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
                if grid[ny][nx] == 0 and (ny, nx) not in visited:
                    new_pos = [ny, nx]
                    new_path = path + [new_pos]

                    if new_pos == end:
                        return new_path

                    visited.add((ny, nx))
                    queue.append((new_pos, new_path))

    return [start]

def greedy_tsp(grid, start, walkable):
    if not walkable or start not in walkable:
        return [start]

    path = [start]
    visited = {tuple(start)}
    current = start

    while len(visited) < len(walkable):
        nearest = None
        min_dist = float('inf')

        for cell in walkable:
            if tuple(cell) not in visited:
                dist = manhattan_distance(current, cell)
                if dist < min_dist:
                    min_dist = dist
                    nearest = cell

        if nearest is None:
            break

        segment = find_shortest_path(grid, current, nearest)
        path.extend(segment[1:])
        visited.add(tuple(nearest))
        current = nearest

    return path

def coords_to_commands(path):
    commands = []
    for i in range(len(path) - 1):
        y1, x1 = path[i]
        y2, x2 = path[i + 1]

        if y2 < y1:
            commands.append("up")
        elif y2 > y1:
            commands.append("down")
        elif x2 < x1:
            commands.append("left")
        elif x2 > x1:
            commands.append("right")

    return commands

@app.get("/api/optimize")
def optimize_path():
    grid = game_state["grid"]
    start = [game_state["rover"]["y"], game_state["rover"]["x"]]

    walkable = find_walkable_cells(grid)
    optimal_path = greedy_tsp(grid, start, walkable)
    commands = coords_to_commands(optimal_path)

    return {
        "path": optimal_path,
        "commands": commands,
        "distance": len(commands),
        "message": "최적 경로 계산 완료"
    }

@app.get("/", response_class=HTMLResponse)
def read_index():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r", encoding="utf-8") as f:
        return f.read()
