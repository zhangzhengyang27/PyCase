"""字符方阵：10×10，字符集 ''AB123''。"""
size, chars = 10, "'AB123'"
for r in range(size):
    row = "".join(chars[(r * c + r + c) % len(chars)] for c in range(size))
    print(row)
