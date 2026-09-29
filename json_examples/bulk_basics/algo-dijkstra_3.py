"""Dijkstra：从 0 号点到各点的最短距离（7 个顶点）。"""
import heapq

graph = {{0: [(1, 7), (2, 9), (3, 14)], 1: [(2, 10), (5, 4)], 2: [(3, 11), (5, 2)], 3: [], 5: [(6, 3)], 6: []}}
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
