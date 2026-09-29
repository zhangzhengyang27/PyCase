"""0-1 背包：容量 30，{{n}} 件物品。"""
weights = [3, 5, 7, 9, 11, 13, 15, 17]
values = [6, 12, 18, 24, 30, 36, 42, 48]
cap = 30
dp = [0] * (cap + 1)
for w, v in zip(weights, values):
    for c in range(cap, w - 1, -1):
        dp[c] = max(dp[c], dp[c - w] + v)
print("最大价值:", dp[cap])
