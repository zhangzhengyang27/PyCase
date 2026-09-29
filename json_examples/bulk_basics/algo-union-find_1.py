"""并查集：8 个元素执行 3 次合并/查询。"""
parent = list(range(8))
rank = [0] * 8

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False
    if rank[ra] < rank[rb]:
        ra, rb = rb, ra
    parent[rb] = ra
    if rank[ra] == rank[rb]:
        rank[ra] += 1
    return True

pairs = [(0, 1), (2, 4), (5, 6)]
for a, b in pairs:
    union(a, b)
print("连通分量数:", len({find(i) for i in range(8)}))
