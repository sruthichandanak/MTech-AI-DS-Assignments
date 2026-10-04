# Indian Cities Distance Graph — Dijkstra's Algorithm

## Overview

The goal of this project is to create a graph of Indian cities and use **Dijkstra's algorithm** to find the shortest-distance route between two cities.

Initially, I looked for datasets containing distances between Indian cities. Kaggle datasets contained very limited information, which was not sufficient to properly build and demonstrate the algorithm.

I then explored open-source options such as **OpenStreetMap**. However, OpenStreetMap provides a very large amount of detailed information, much of which was unnecessary for this assignment.

After exploring other sources, I found the PDF **`ROAD_MAP_2026.pdf`**, which contains distances between Indian cities in a **matrix format**. This PDF is included in the project as the original source/reference for the distance data. I extracted the distance information from the matrix with the help of AI and converted it into a usable dataset.

The resulting dataset contains approximately **1,220 distance values** between 50 Indian cities.

---

## Why the Original Dataset Could Not Be Used Directly

In the original distance matrix, almost every city has a direct distance value to every other city.

For example:

```text
City A → City B
City A → City C
City A → City D
...
```

If every city is directly connected to every other city, there is very little need to demonstrate Dijkstra's algorithm because the distance between the source and destination is already directly available.

Therefore, the matrix was converted into a **sparser graph**, where each city is connected only to a smaller number of relevant neighbouring cities.

The goal was to create approximately **100–150 meaningful edges** while still keeping the graph connected.

---

## Creating Meaningful Edges

The idea was to keep an edge between two cities only when there is no important intermediate city that should logically come between them.

For example:

```text
Delhi → Jaipur
```

can be considered a direct edge.

However:

```text
Delhi → Udaipur
```

does not need to be a direct edge if Jaipur or another intermediate city lies naturally along that route.

The cleaning rule used was:

> Keep a link between A and B only if there is no third city C on the way.

More specifically, if:

```text
distance(A, C) + distance(C, B)
```

is only slightly greater than:

```text
distance(A, B)
```

(within approximately **10–15%**), then C is considered to lie on the route between A and B, and the direct A → B link is removed.

This creates a graph where edges represent more meaningful neighbouring-city connections instead of connecting every city directly to every other city.

---

## Data Cleaning

The distance matrix was cleaned using:

```text
data_cleaning.py
```

The cleaning process produced the following results:

```text
Step 1: 50 cities, 1224 pairs loaded

Step 2: 1218 usable pairs after removing doubtful values

Step 3: 157 edges after keeping each city's 5 nearest

Step 4: 103 edges after dropping links that skip a city

Step 5: graph is connected - every city can reach every other

Step 6: saved 103 edges between 50 cities to india_graph_edges.csv
```

### Final Graph

The final graph contains:

- **50 cities**
- **103 edges**
- A connected graph
- Every city can reach every other city through one or more intermediate cities

The cleaned graph is stored in:

```text
india_graph_edges.csv
```

---

## Applying Dijkstra's Algorithm

Once the graph was created, **Dijkstra's shortest-path algorithm** was applied to find the shortest distance between two cities, even when there is no direct edge between them.

For example:

```bash
python dijkstra.py Hyderabad Srinagar
```

Output:

```text
Hyderabad to Srinagar: 2534 km

Hyderabad -> Nagpur -> Jabalpur -> Agra -> Delhi -> Chandigarh -> Jammu -> Srinagar
```

This demonstrates the purpose of creating the sparse graph: Dijkstra's algorithm finds a route through intermediate cities rather than simply using a direct distance from the original matrix.

---

## How the Dijkstra Code Works

The implementation uses a **priority queue** (`heapq`) and follows the standard Dijkstra / Uniform-Cost Search approach.

### 1. Building the Graph

The `load_graph()` function reads `india_graph_edges.csv`.

Each row contains:

```text
Origin, Destination, Distance
```

For every edge, the code adds both directions:

```python
graph.setdefault(a, []).append((b, km))
graph.setdefault(b, []).append((a, km))
```

This is because the graph represents two-way travel between cities.

The resulting structure is approximately:

```text
city → [(neighbour, distance), ...]
```

### 2. Finding the Shortest Distance

The `dijkstra()` function maintains:

- `dist` — the best known distance from the source to each city
- `prev` — the previous city on the shortest known route
- `frontier` — a priority queue containing cities ordered by their current distance
- `done` — cities whose shortest distance has already been finalized

The priority queue is initialized with:

```python
frontier = [(0, source)]
```

The algorithm repeatedly removes the city with the smallest known distance.

For each neighbouring city, it calculates:

```text
new distance = current distance + edge distance
```

If this new distance is smaller than the previously known distance, the value is updated and the neighbour is added to the priority queue.

The algorithm stops once the destination city is removed from the priority queue, because its shortest distance is then finalized.

### 3. Reconstructing the Route

The `prev` dictionary stores the city from which each city was reached on the shortest route.

The `build_route()` function starts at the destination and walks backwards through `prev` until it reaches the source.

For example, the calculated route can be:

```text
Hyderabad → Nagpur → Jabalpur → Agra → Delhi → Chandigarh → Jammu → Srinagar
```

---

## Code Structure

```text
dijistra_indian_cities/
│
├── ROAD_MAP_2026.pdf
├── data_cleaning.py
├── dijkstra.py
├── india_graph_edges.csv
└── README.md
```

### `ROAD_MAP_2026.pdf`

The original PDF containing the Indian city distance matrix used as the source for the dataset.

### `data_cleaning.py`

Cleans the original distance matrix and converts the dense set of city-to-city distances into a smaller, meaningful graph.

### `india_graph_edges.csv`

Contains the final **103 edges between 50 cities** used by the Dijkstra implementation.

### `dijkstra.py`

Loads the graph and calculates the shortest route between two cities using Dijkstra's algorithm.

### `README.md`

Documents the dataset creation, cleaning process, graph construction, and Dijkstra implementation.

---

## Running the Project

### 1. Clean the Data

```bash
python data_cleaning.py
```

This generates:

```text
india_graph_edges.csv
```

### 2. Run Dijkstra

```bash
python dijkstra.py <source_city> <destination_city>
```

Example:

```bash
python dijkstra.py Hyderabad Srinagar
```

Example output:

```text
Hyderabad to Srinagar: 2534 km
Hyderabad -> Nagpur -> Jabalpur -> Agra -> Delhi -> Chandigarh -> Jammu -> Srinagar
```

---

## Result

The original matrix provided direct distances between a large number of city pairs, making it unsuitable for meaningfully demonstrating a shortest-path algorithm.

By reducing the dense matrix to a connected graph of **50 cities and 103 meaningful edges**, the project creates a situation where the shortest route may require travelling through several intermediate cities.

Dijkstra's algorithm can then determine:

1. The minimum total distance between two cities.
2. The intermediate cities used along the shortest route.
3. A route even when there is no direct edge between the source and destination.

This demonstrates the practical use of **Dijkstra's shortest-path algorithm on a real-world-inspired Indian city distance dataset**.
