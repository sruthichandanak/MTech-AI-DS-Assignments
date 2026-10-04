"""
Dijkstra (uniform-cost search) with a priority queue on india_graph_edges.csv.

Run:  python dijkstra.py Hyderabad Kolkata
"""
import csv
import heapq
import sys


# ---- Step A: build the graph from the CSV ----------------------------------
def load_graph(path="india_graph_edges.csv"):
    graph = {}                                   # city -> list of (neighbour, km)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            a, b, km = row["Origin"], row["Destination"], float(row["Distance"])
            graph.setdefault(a, []).append((b, km))   # A -> B
            graph.setdefault(b, []).append((a, km))   # B -> A (roads are two-way)
    return graph


# ---- Step B: Dijkstra with a priority queue --------------------------------
def dijkstra(graph, source, destination):
    dist = {source: 0}              # best known cost to reach each city
    prev = {}                       # which city we came from on the best route
    frontier = [(0, source)]        # priority queue of (cost, city)
    done = set()                    # cities whose cost is final

    while frontier:
        cost, city = heapq.heappop(frontier)   # cheapest entry comes out first

        if city in done:            # outdated entry: a cheaper one was handled earlier
            continue
        done.add(city)

        if city == destination:     # its cost is now final, so stop
            break

        for neighbour, km in graph[city]:
            new_cost = cost + km
            if new_cost < dist.get(neighbour, float("inf")):
                dist[neighbour] = new_cost
                prev[neighbour] = city
                heapq.heappush(frontier, (new_cost, neighbour))

    return dist, prev


# ---- Step C: build the route by walking back through prev ------------------
def build_route(prev, source, destination):
    route = [destination]
    while route[-1] != source:
        route.append(prev[route[-1]])
    return route[::-1]


# ---- Run it ----------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python dijkstra.py <from city> <to city>")

    graph = load_graph()
    source, destination = sys.argv[1], sys.argv[2]
    for city in (source, destination):
        if city not in graph:
            sys.exit(f"'{city}' is not in the graph. Check the spelling.")

    dist, prev = dijkstra(graph, source, destination)

    if destination not in dist:
        print("No route found.")
    else:
        route = build_route(prev, source, destination)
        print(f"{source} to {destination}: {dist[destination]:.0f} km")
        print(" -> ".join(route))