# UGV Path Planning: Static Obstacles (A*)

An Unmanned Ground Vehicle (UGV) must travel from a start node to a goal node on a 70 x 70 km map (1 cell = 1 km) by the shortest distance. All obstacles are known in advance.

## Files

```
static/
├── a_star_approach.py   # the planner
├── ugv_paths.png        # output picture (one map per density)
└── README.md
```

Keep the file name free of `*`. Python cannot import a module with `*` in its name, and the dynamic version imports this file.

## Requirements

- Python 3.9+
- `numpy`, `matplotlib`

```
pip install numpy matplotlib
```

## How to run

From the `static` folder:

```
python a_star_approach.py                    # default: start (2,3), goal (67,66)
python a_star_approach.py 5 5 60 65          # custom: start_row start_col goal_row goal_col
```

It prints a table of Measures of Effectiveness for the three densities and saves `ugv_paths.png`. Check that the `plt.savefig(...)` line points to a folder that exists on your machine.

## Idea

A\* always expands the square that looks most promising. It scores each square as:

```
score = distance travelled so far + estimated distance still to go
```

The estimate (the heuristic) is the octile distance, which never overestimates the true distance. Because of that, A\* returns the shortest path while checking far fewer squares than a blind search.

## Design choices

- **Grid:** 70 x 70, one cell = 1 km.
- **Movement:** 8 directions. A straight step costs 1 km and a diagonal step costs about 1.41 km.
- **Corner rule:** the UGV cannot cut diagonally between two touching obstacles.
- **Obstacle density:** random, at three levels: Low (10%), Medium (20%), High (30%).
- **Reachability:** if a random map has no route, a new map is generated.
- **Input:** user-specified start and goal squares.

## Measures of Effectiveness (MoE)

- Path length (km) and detour over the straight-line distance
- Number of waypoints and number of turns
- Squares checked by the search and computation time
- Minimum clearance from obstacles

## Results (start (2,3), goal (67,66))

| Measure | Low (10%) | Medium (20%) | High (30%) |
|---|---|---|---|
| Path length (km) | 96.95 | 103.98 | 127.36 |
| Straight-line distance (km) | 90.52 | 90.52 | 90.52 |
| Detour over straight line | 7.1% | 14.9% | 40.7% |
| Turns | 18 | 41 | 53 |
| Squares checked | 738 | 1325 | 2173 |
| Compute time (ms) | 5.7 | 8.9 | 13.7 |

More obstacles mean longer paths, more turns and more search work. Times vary a little from machine to machine.

## Possible extensions

- **Weighted A\*:** multiply the heuristic by a factor above 1 for faster search at the cost of slightly longer paths.
- **Terrain costs:** make squares such as sand or slopes more expensive to cross.
