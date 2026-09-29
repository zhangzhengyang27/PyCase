"""矩阵旋转：8×8 顺时针 90°。"""
n = 8
mat = [[(i * n + j) % 5 for j in range(n)] for i in range(n)]
print("旋转前:", mat[0])
for layer in range(n // 2):
    first, last = layer, n - 1 - layer
    for i in range(first, last):
        off = i - first
        top = mat[first][i]
        mat[first][i] = mat[last - off][first]
        mat[last - off][first] = mat[last][last - off]
        mat[last][last - off] = mat[i][last]
        mat[i][last] = top
print("旋转后:", mat[0])
