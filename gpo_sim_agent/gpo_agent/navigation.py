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
    """
    8-direction A* pathfinding on grid with Octile heuristic and Clearance Penalty.
    - Straight step cost: 1.0
    - Diagonal step cost: 1.414
    - Clearance penalty: +0.5 for cells adjacent to obstacles to avoid wall hugging and corner snagging.
    """
    if start == goal:
        return [start]
    if start in blocked or goal in blocked:
        return []

    # Octile distance heuristic for 8-direction grid (admissible & consistent)
    def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + 0.414 * min(dx, dy)

    # Precompute cells adjacent to blocked obstacles (Clearance Penalty)
    near_blocked: set[tuple[int, int]] = set()
    for bx, by in blocked:
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox == 0 and oy == 0:
                    continue
                adj = (bx + ox, by + oy)
                if 0 <= adj[0] < width and 0 <= adj[1] < height and adj not in blocked:
                    near_blocked.add(adj)

    # 8-direction movements: 4 cardinal (1.0) and 4 diagonal (1.414)
    neighbors = (
        (1, 0, 1.0),
        (-1, 0, 1.0),
        (0, 1, 1.0),
        (0, -1, 1.0),
        (1, 1, 1.414),
        (1, -1, 1.414),
        (-1, 1, 1.414),
        (-1, -1, 1.414)
    )

    frontier: list[tuple[float, float, tuple[int, int]]] = [(heuristic(start, goal), 0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost: dict[tuple[int, int], float] = {start: 0.0}

    while frontier:
        _, current_cost, current = heappop(frontier)
        if current == goal:
            break
        if current_cost > cost[current]:
            continue

        cx, cy = current
        for dx, dy, step_cost in neighbors:
            nxt = (cx + dx, cy + dy)
            if not (0 <= nxt[0] < width and 0 <= nxt[1] < height) or nxt in blocked:
                continue

            # Prevent cutting through diagonal obstacles (squeezing between two corners)
            if dx != 0 and dy != 0:
                if (cx + dx, cy) in blocked and (cx, cy + dy) in blocked:
                    continue

            # Clearance penalty (+0.5) if cell is next to a blocked cell
            penalty = 0.5 if nxt in near_blocked else 0.0
            candidate = current_cost + step_cost + penalty

            if candidate < cost.get(nxt, 1e9):
                cost[nxt] = candidate
                came_from[nxt] = current
                heappush(frontier, (candidate + heuristic(nxt, goal), candidate, nxt))

    if goal not in came_from:
        return []

    path, curr = [], goal
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    return list(reversed(path))


def cell_at(point: tuple[float, float], cell_size: int = 32) -> tuple[int, int]:
    return int(point[0] // cell_size), int(point[1] // cell_size)


def center_of(cell: tuple[int, int], cell_size: int = 32) -> tuple[float, float]:
    return (cell[0] + .5) * cell_size, (cell[1] + .5) * cell_size
