"""字符方阵：13×13，字符集 ''·:*#''。"""
size, chars = 13, "'·:*#'"
for r in range(size):
    row = "".join(chars[(r * c + r + c) % len(chars)] for c in range(size))
    print(row)
