"""0-1 背包：容量 10，4 件物品。"""
weights = [2, 3, 5, 7]
values = [3, 4, 5, 9]
cap = 10
dp = [0] * (cap + 1)
for w, v in zip(weights, values):
    for c in range(cap, w - 1, -1):
        dp[c] = max(dp[c], dp[c - w] + v)
print("最大价值:", dp[cap])
