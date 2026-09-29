"""并查集：9 个元素执行 4 次合并/查询。"""
parent = list(range(9))
rank = [0] * 9

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

pairs = [(0, 2), (2, 5), (5, 6)]
for a, b in pairs:
    union(a, b)
print("连通分量数:", len({find(i) for i in range(9)}))
