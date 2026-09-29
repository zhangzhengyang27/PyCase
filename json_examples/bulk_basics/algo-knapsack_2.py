"""0-1 背包：容量 15，{{n}} 件物品。"""
weights = [4, 5, 6, 2, 3]
values = [7, 8, 9, 2, 4]
cap = 15
dp = [0] * (cap + 1)
for w, v in zip(weights, values):
    for c in range(cap, w - 1, -1):
        dp[c] = max(dp[c], dp[c - w] + v)
print("最大价值:", dp[cap])
