"""考拉兹序列：起点 97，最长链搜索到 2000。"""
def collatz_len(n):
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps

print("起点 97 步数:", collatz_len(97))
best = max(range(1, 2000), key=lambda n: (collatz_len(n), -n))
print(f"1~2000 中链最长: {best} ({collatz_len(best)} 步)")
