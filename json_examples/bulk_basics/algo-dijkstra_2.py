"""Dijkstra：从 0 号点到各点的最短距离（6 个顶点）。"""
import heapq

graph = {{0: [(1, 2), (2, 6)], 1: [(3, 5)], 2: [(3, 1)], 3: [(4, 2), (5, 6)], 4: [], 5: []}}
dist = {0: 0}
heap = [(0, 0)]
while heap:
    d, u = heapq.heappop(heap)
    if d > dist.get(u, float("inf")):
        continue
    for v, w in graph.get(u, []):
        nd = d + w
        if nd < dist.get(v, float("inf")):
            dist[v] = nd
            heapq.heappush(heap, (nd, v))
print(dict(sorted(dist.items())))
