"""
UGV navigation with DYNAMIC, a-priori UNKNOWN obstacles: A* with replanning.

Loop at every step:  sense -> check path -> (replan with A* if threatened) -> move one cell
-> obstacles move.

Usage:  python ugv_dynamic.py
        python ugv_dynamic.py 2 3 67 66   (start_row start_col goal_row goal_col)
"""
import math, random, sys, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "static"))
from a_approach import astar, SIZE, DENSITY, MOVES

SENSOR_RANGE = 5      # km: UGV only sees obstacles this close
MOVING_SHARE = 0.20   # share of obstacles that move (1 cell per step, randomly)
LOOKAHEAD = 8         # replan if an obstacle blocks the next 8 cells of the path
MEMORY = 20           # steps a sensed obstacle stays on the UGV's map once out of view
MAX_STEPS = 1500
RUNS = 20             # runs per density for averaged results


def build_world(density, start, goal, rng):
    grid = (rng.random((SIZE, SIZE)) < density).astype(int)
    grid[start] = 0
    grid[goal] = 0
    obs = np.argwhere(grid == 1)
    k = int(len(obs) * MOVING_SHARE)
    mobile = {tuple(obs[i]) for i in rng.choice(len(obs), k, replace=False)}
    return grid, mobile


def move_obstacles(grid, mobile, ugv, goal, rng):
    """Each moving obstacle takes one random step to a free neighbouring cell."""
    new_mobile, contacts = set(), 0
    for (r, c) in list(mobile):
        dr, dc, _ = MOVES[rng.integers(len(MOVES))]
        nr, nc = r + dr, c + dc
        ok = 0 <= nr < SIZE and 0 <= nc < SIZE and grid[nr, nc] == 0 and (nr, nc) != goal
        if ok and (nr, nc) == ugv:
            contacts += 1            # obstacle tried to hit the UGV -> counted as a collision
            ok = False
        if ok:
            grid[r, c], grid[nr, nc] = 0, 1
            new_mobile.add((nr, nc))
        else:
            new_mobile.add((r, c))
    return new_mobile, contacts


def grow(mask, radius):
    """Expand a 0/1 mask by `radius` cells in every direction."""
    p = np.pad(mask, radius)
    out = np.zeros_like(mask)
    for dr in range(2 * radius + 1):
        for dc in range(2 * radius + 1):
            out |= p[dr:dr + SIZE, dc:dc + SIZE]
    return out


def sense(true_grid, known, last_seen, moved_at, pos, t):
    """Update the UGV's map. A cell that was seen empty one step ago and now holds an
    obstacle means an obstacle just moved in -> remember when (moved_at)."""
    r0, c0 = pos
    for r in range(max(0, r0 - SENSOR_RANGE), min(SIZE, r0 + SENSOR_RANGE + 1)):
        for c in range(max(0, c0 - SENSOR_RANGE), min(SIZE, c0 + SENSOR_RANGE + 1)):
            if math.hypot(r - r0, c - c0) <= SENSOR_RANGE:
                if last_seen[r, c] == t - 1 and known[r, c] == 0 and true_grid[r, c] == 1:
                    moved_at[r, c] = t
                known[r, c] = true_grid[r, c]
                last_seen[r, c] = t


def simulate(density, start, goal, seed, margin=1, moving_memory=1):
    rng = np.random.default_rng(seed)
    grid, mobile = build_world(density, start, goal, rng)
    initial = grid.copy()
    ideal_path, ideal_len, _ = astar(initial, start, goal)   # hindsight baseline (initial map, fully known)
    if ideal_path is None:
        return None

    known = np.zeros((SIZE, SIZE), dtype=int)       # UGV starts knowing nothing
    last_seen = np.full((SIZE, SIZE), -10**9)
    moved_at = np.full((SIZE, SIZE), -10**9)        # when an obstacle was last seen moving into a cell
    pos, trail, path = start, [start], []
    dist = 0.0
    replans = collisions = waits = 0
    compute_ms = 0.0
    nodes = 0

    for t in range(MAX_STEPS):
        if pos == goal:
            break
        sense(grid, known, last_seen, moved_at, pos, t)
        plan_grid = np.where((known == 1) & (t - last_seen <= MEMORY), 1, 0)
        plan_grid[pos] = 0
        plan_grid[goal] = 0

        moving = ((known == 1) & (t - moved_at <= moving_memory)).astype(int)
        safe_grid = plan_grid | grow(moving, margin)     # keep extra distance from moving obstacles
        safe_grid[pos] = 0
        safe_grid[goal] = 0
        threatened = (not path) or any(safe_grid[p] for p in path[:LOOKAHEAD])
        if threatened:
            t0 = time.perf_counter()
            new_path, _, exp = astar(safe_grid, pos, goal)
            if not new_path:                       # no route with margin: accept a tighter one
                new_path, _, exp2 = astar(plan_grid, pos, goal)
                exp += exp2
            compute_ms += (time.perf_counter() - t0) * 1000
            replans += 1
            nodes += exp
            path = new_path[1:] if new_path else []

        if path:
            nxt = path[0]
            dr, dc = nxt[0] - pos[0], nxt[1] - pos[1]
            blocked = grid[nxt] == 1 or (dr and dc and (grid[pos[0] + dr, pos[1]] or grid[pos[0], pos[1] + dc]))
            if blocked:
                path = []                # surprise obstacle: stay put and replan next step
                waits += 1
            else:
                dist += math.hypot(dr, dc)
                pos = nxt
                path.pop(0)
                trail.append(pos)
        else:
            waits += 1                   # no known route right now: wait for obstacles to move

        mobile, hit = move_obstacles(grid, mobile, pos, goal, rng)
        collisions += hit

    return {
        "reached": pos == goal, "dist": dist, "ideal": ideal_len, "replans": replans,
        "waits": waits, "collisions": collisions, "time_ms": compute_ms,
        "steps": len(trail) - 1, "nodes": nodes, "trail": trail,
        "ideal_path": ideal_path, "initial": initial, "final": grid,
    }


def summarise(res):
    ok = [r for r in res if r["reached"]]
    return {
        "Runs": len(res),
        "Success rate (%)": round(100 * len(ok) / len(res), 1),
        "Avg distance travelled (km)": round(np.mean([r["dist"] for r in ok]), 1),
        "Avg ideal path, all known (km)": round(np.mean([r["ideal"] for r in ok]), 1),
        "Avg extra distance (%)": round(np.mean([100 * (r["dist"] / r["ideal"] - 1) for r in ok]), 1),
        "Avg replans": round(np.mean([r["replans"] for r in ok]), 1),
        "Avg waiting steps": round(np.mean([r["waits"] for r in ok]), 1),
        "Avg collisions per run": round(np.mean([r["collisions"] for r in res]), 2),
        "Runs with a collision": sum(r["collisions"] > 0 for r in res),
        "Avg planning time (ms)": round(np.mean([r["time_ms"] for r in ok]), 1),
    }


def main():
    a = list(map(int, sys.argv[1:5])) if len(sys.argv) >= 5 else [2, 3, 67, 66]
    start, goal = (a[0], a[1]), (a[2], a[3])
    modes = {"No margin": 0, "Safety margin": 1}
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    table = {}
    for i, (mode, margin) in enumerate(modes.items()):
        for j, (name, dens) in enumerate(DENSITY.items()):
            res = [r for r in (simulate(dens, start, goal, s, margin) for s in range(RUNS)) if r]
            table[f"{name} / {mode}"] = summarise(res)
            r = [x for x in res if x["reached"]][0]
            ax = axes[i][j]
            ax.imshow(r["initial"], cmap="Greys", alpha=0.35, origin="upper")
            ax.imshow(np.ma.masked_where(r["final"] == 0, r["final"]), cmap="Reds", alpha=0.6, origin="upper")
            ax.plot([p[1] for p in r["ideal_path"]], [p[0] for p in r["ideal_path"]], "c--", lw=1.2, label="Ideal (all known)")
            ax.plot([p[1] for p in r["trail"]], [p[0] for p in r["trail"]], "b-", lw=2, label="UGV actual path")
            ax.scatter(start[1], start[0], c="lime", s=120, edgecolors="k", zorder=5)
            ax.scatter(goal[1], goal[0], c="gold", s=120, edgecolors="k", zorder=5)
            ax.set_title(f"{name} density, {mode}: {r['dist']:.1f} km, {r['replans']} replans")
            ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig("/Users/malvika/Documents/mtech/ai/ugv/dynamic/ugv_dynamic_paths.png", dpi=100)

    keys = list(next(iter(table.values())).keys())
    print(f"{'':32s}" + "".join(f"{n.replace(' / ', ' ').replace('Safety margin','Safe').replace('No margin','NoMgn'):>13s}" for n in table))
    for k in keys:
        print(f"{k:32s}" + "".join(f"{str(table[n][k]):>13s}" for n in table))


if __name__ == "__main__":
    main()