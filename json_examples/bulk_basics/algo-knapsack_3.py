"""0-1 背包：容量 20，{{n}} 件物品。"""
weights = [5, 6, 8, 3, 4, 7]
values = [10, 12, 15, 4, 6, 11]
cap = 20
dp = [0] * (cap + 1)
for w, v in zip(weights, values):
    for c in range(cap, w - 1, -1):
        dp[c] = max(dp[c], dp[c - w] + v)
print("最大价值:", dp[cap])
