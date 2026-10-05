from heapq import heappop, heappush
from math import hypot


def move_toward(player: tuple[float, float], target: tuple[float, float], stride: float) -> tuple[float, float]:
    """Move one bounded step toward an image-derived target coordinate."""
    dx, dy = target[0] - player[0], target[1] - player[1]
    distance = hypot(dx, dy)
    if distance <= stride or distance == 0:
        return target
    return player[0] + dx / distance * stride, player[1] + dy / distance * stride


def find_path(start: tuple[int, int], goal: tuple[int, int], blocked: set[tuple[int, int]],
              width: int = 20, height: int = 11) -> list[tuple[int, int]]:
    """A* on the pixel-scanned minimap grid; returns cell coordinates including start."""
    def heuristic(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
    frontier = [(heuristic(start, goal), 0, start)]
    came_from, cost = {start: None}, {start: 0}
    while frontier:
        _, current_cost, current = heappop(frontier)
        if current == goal: break
        if current_cost != cost[current]: continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = current[0] + dx, current[1] + dy
            if not (0 <= nxt[0] < width and 0 <= nxt[1] < height) or nxt in blocked: continue
            candidate = current_cost + 1
            if candidate < cost.get(nxt, 10**9):
                cost[nxt], came_from[nxt] = candidate, current
                heappush(frontier, (candidate + heuristic(nxt, goal), candidate, nxt))
    if goal not in came_from: return []
    path, current = [], goal
    while current is not None:
        path.append(current); current = came_from[current]
    return list(reversed(path))


def cell_at(point: tuple[float, float], cell_size: int = 32) -> tuple[int, int]:
    return int(point[0] // cell_size), int(point[1] // cell_size)


def center_of(cell: tuple[int, int], cell_size: int = 32) -> tuple[float, float]:
    return (cell[0] + .5) * cell_size, (cell[1] + .5) * cell_size
