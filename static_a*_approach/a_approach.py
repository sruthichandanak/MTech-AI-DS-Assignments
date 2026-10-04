"""
UGV shortest-path planner on a 70x70 km battlefield grid (1 cell = 1 km).
Algorithm: A* search, 8-direction movement, no cutting through obstacle corners.
Usage:  python ugv_planner.py            (uses default start/goal)
        python ugv_planner.py 2 3 67 66  (start_row start_col goal_row goal_col)
"""
import heapq, math, random, sys, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIZE = 70
DENSITY = {"Low": 0.10, "Medium": 0.20, "High": 0.30}
MOVES = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
         (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
         (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]


def make_grid(density, start, goal, seed):
    rng = np.random.default_rng(seed)
    grid = (rng.random((SIZE, SIZE)) < density).astype(int)  # 1 = obstacle
    grid[start] = 0
    grid[goal] = 0
    return grid


def heuristic(a, b):
    # Octile distance: exact cost on an empty 8-direction grid, never overestimates
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)


def astar(grid, start, goal):
    open_heap = [(heuristic(start, goal), 0.0, start)]
    g = {start: 0.0}
    parent = {}
    closed = set()
    expanded = 0
    while open_heap:
        _, gc, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        if cur == goal:
            path = [cur]
            while cur in parent:
                cur = parent[cur]
                path.append(cur)
            return path[::-1], gc, expanded
        for dr, dc, cost in MOVES:
            nr, nc = cur[0] + dr, cur[1] + dc
            if not (0 <= nr < SIZE and 0 <= nc < SIZE) or grid[nr, nc]:
                continue
            # block diagonal moves that squeeze between two obstacles
            if dr and dc and (grid[cur[0] + dr, cur[1]] or grid[cur[0], cur[1] + dc]):
                continue
            nxt = (nr, nc)
            ng = gc + cost
            if ng < g.get(nxt, float("inf")):
                g[nxt] = ng
                parent[nxt] = cur
                heapq.heappush(open_heap, (ng + heuristic(nxt, goal), ng, nxt))
    return None, float("inf"), expanded


def count_turns(path):
    turns = 0
    for i in range(2, len(path)):
        d1 = (path[i-1][0] - path[i-2][0], path[i-1][1] - path[i-2][1])
        d2 = (path[i][0] - path[i-1][0], path[i][1] - path[i-1][1])
        turns += d1 != d2
    return turns


def min_clearance(grid, path):
    obs = np.argwhere(grid == 1)
    if len(obs) == 0:
        return float("inf")
    return min(np.min(np.hypot(obs[:, 0] - r, obs[:, 1] - c)) for r, c in path)


def run(start, goal):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    results = []
    for ax, (name, dens) in zip(axes, DENSITY.items()):
        seed = 0
        while True:  # regenerate until the goal is reachable
            grid = make_grid(dens, start, goal, seed)
            t0 = time.perf_counter()
            path, cost, expanded = astar(grid, start, goal)
            t = (time.perf_counter() - t0) * 1000
            if path:
                break
            seed += 1
        straight = math.hypot(goal[0] - start[0], goal[1] - start[1])
        results.append({
            "Density": f"{name} ({int(dens*100)}%)",
            "Actual obstacle %": round(100 * grid.mean(), 1),
            "Path length (km)": round(cost, 2),
            "Straight line (km)": round(straight, 2),
            "Efficiency (straight/path)": round(straight / cost, 3),
            "Detour (%)": round(100 * (cost / straight - 1), 1),
            "Waypoints": len(path),
            "Turns": count_turns(path),
            "Nodes expanded": expanded,
            "Search space used (%)": round(100 * expanded / (SIZE * SIZE - grid.sum()), 1),
            "Compute time (ms)": round(t, 1),
            "Min clearance (km)": round(min_clearance(grid, path), 2),
            "Seeds tried": seed + 1,
        })
        ax.imshow(grid, cmap="Greys", origin="upper")
        ax.plot([p[1] for p in path], [p[0] for p in path], "r-", lw=2)
        ax.scatter(start[1], start[0], c="lime", s=120, edgecolors="k", zorder=5, label="Start")
        ax.scatter(goal[1], goal[0], c="blue", s=120, edgecolors="k", zorder=5, label="Goal")
        ax.set_title(f"{name} density - path {cost:.1f} km")
        ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig("/Users/malvika/Documents/mtech/ai/ugv/ugv_paths.png", dpi=110)
    return results


if __name__ == "__main__":
    a = list(map(int, sys.argv[1:5])) if len(sys.argv) >= 5 else [2, 3, 67, 66]
    start, goal = (a[0], a[1]), (a[2], a[3])
    res = run(start, goal)
    keys = list(res[0].keys())
    for k in keys:
        print(f"{k:28s}" + "".join(f"{str(r[k]):>18s}" for r in res))