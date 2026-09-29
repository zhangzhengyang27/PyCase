"""字符方阵：11×11，字符集 ''░▒▓''。"""
size, chars = 11, "'░▒▓'"
for r in range(size):
    row = "".join(chars[(r * c + r + c) % len(chars)] for c in range(size))
    print(row)
