"""字符方阵：9×9，字符集 ''◆◇''。"""
size, chars = 9, "'◆◇'"
for r in range(size):
    row = "".join(chars[(r * c + r + c) % len(chars)] for c in range(size))
    print(row)
