"""
Reduce the full distance chart (1,225 city pairs) to a sparse road graph.

Why: the chart gives a distance for EVERY pair of cities. If we used all of
them as edges, Dijkstra would always take the direct edge. A real road network
only joins neighbouring cities, so we keep a small set of "direct road" edges.

Steps
  1. Load the table of all pairs into a dictionary.
  2. Remove values we do not trust (nothing is added or filled in by hand).
  3. Rule 1 - keep each city's K nearest cities.
  4. Rule 2 - drop an edge if another city lies on the way.
  5. Check the graph is connected. If it is not, keep only the largest
     connected group of cities and report the cities that were removed.
  6. Save the edges to a CSV.

Run:  python build_graph.py
Needs: india_distances_clean.csv in the same folder.
"""
import csv
import os
from collections import defaultdict, deque

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, "india_distances_clean.csv")
OUTPUT = os.path.join(HERE, "india_graph_edges.csv")

K = 5            # Rule 1: how many nearest neighbours to keep per city
TOLERANCE = 0.10 # Rule 2: "on the way" if the detour adds less than 10%

# Chart values that look like printing errors - we do not use them
DOUBTFUL = {
    frozenset(p) for p in [
        ("Udhagamandalam", "Dispur"), ("Shillong", "Bengaluru"),
        ("Udaipur", "Darjeeling"), ("Panaji", "Lucknow"),
        ("Mount Abu", "Bengaluru"), ("Shimla", "Mumbai"),
    ]
}


# ---------------------------------------------------------------- step 1 ----
def load_all_pairs(path):
    """Return {frozenset({city_a, city_b}): distance_km}."""
    pairs = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["distance_km"].strip():
                pairs[frozenset((row["city_a"], row["city_b"]))] = float(row["distance_km"])
    return pairs


# ---------------------------------------------------------------- step 2 ----
def clean(pairs):
    return {p: d for p, d in pairs.items() if p not in DOUBTFUL}


def distance(pairs, a, b):
    """Distance between two cities, or None if we do not have one."""
    return pairs.get(frozenset((a, b)))


# ---------------------------------------------------------------- step 3 ----
def nearest_neighbours(pairs, cities, k=K):
    """Rule 1: for each city keep its k closest cities. Returns a set of edges."""
    edges = set()
    for city in cities:
        others = [(distance(pairs, city, c), c) for c in cities if c != city]
        others = sorted((d, c) for d, c in others if d is not None)
        for _, nearest in others[:k]:
            edges.add(frozenset((city, nearest)))   # frozenset = same edge both ways
    return edges


# ---------------------------------------------------------------- step 4 ----
def city_in_between(pairs, cities, a, b, tol=TOLERANCE):
    """
    True if some city C lies on the way from A to B, meaning
    dist(A,C) + dist(C,B) is no more than (1 + tol) * dist(A,B).
    """
    d_ab = distance(pairs, a, b)
    for c in cities:
        if c in (a, b):
            continue
        d_ac, d_cb = distance(pairs, a, c), distance(pairs, c, b)
        if d_ac is None or d_cb is None:
            continue
        if d_ac < d_ab and d_cb < d_ab and d_ac + d_cb <= d_ab * (1 + tol):
            return True
    return False


def drop_skip_edges(pairs, cities, edges):
    kept = set()
    for edge in edges:
        a, b = tuple(edge)
        if not city_in_between(pairs, cities, a, b):
            kept.add(edge)
    return kept


# ---------------------------------------------------------------- step 5 ----
def connected_groups(cities, edges):
    """Breadth-first search to find groups of cities that can reach each other."""
    adj = defaultdict(set)
    for edge in edges:
        a, b = tuple(edge)
        adj[a].add(b)
        adj[b].add(a)
    seen, groups = set(), []
    for start in cities:
        if start in seen:
            continue
        group, queue = set(), deque([start])
        while queue:
            c = queue.popleft()
            if c in group:
                continue
            group.add(c)
            queue.extend(adj[c] - group)
        seen |= group
        groups.append(sorted(group))
    return groups


# ------------------------------------------------------------------ main ----
def main():
    all_pairs = load_all_pairs(INPUT)
    cities = sorted({c for p in all_pairs for c in p})
    print(f"Step 1: {len(cities)} cities, {len(all_pairs)} pairs loaded")

    pairs = clean(all_pairs)
    print(f"Step 2: {len(pairs)} usable pairs after removing doubtful values")

    edges = nearest_neighbours(pairs, cities)
    print(f"Step 3: {len(edges)} edges after keeping each city's {K} nearest")

    edges = drop_skip_edges(pairs, cities, edges)
    print(f"Step 4: {len(edges)} edges after dropping links that skip a city")

    groups = connected_groups(cities, edges)
    if len(groups) == 1:
        print("Step 5: graph is connected - every city can reach every other")
    else:
        main_group = set(max(groups, key=len))
        removed = [c for c in cities if c not in main_group]
        edges = {e for e in edges if e <= main_group}
        cities = sorted(main_group)
        print(f"Step 5: graph had {len(groups)} separate groups. Kept the largest "
              f"({len(cities)} cities) and removed: {', '.join(removed)}")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Origin", "Destination", "Distance"])
        for a, b in sorted(tuple(sorted(e)) for e in edges):
            writer.writerow([a, b, int(distance(pairs, a, b))])
    print(f"Step 6: saved {len(edges)} edges between {len(cities)} cities "
          f"to {os.path.basename(OUTPUT)}")


if __name__ == "__main__":
    main()