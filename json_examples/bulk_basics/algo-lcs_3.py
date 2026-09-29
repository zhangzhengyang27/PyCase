"""LCS：'{a}' 与 '{b}' 的最长公共子序列。"""
A, B = "'kitten'", "'sitting'"
dp = [[0] * (len(B) + 1) for _ in range(len(A) + 1)]
for i in range(1, len(A) + 1):
    for j in range(1, len(B) + 1):
        dp[i][j] = dp[i - 1][j - 1] + 1 if A[i - 1] == B[j - 1] else max(dp[i - 1][j], dp[i][j - 1])
i, j, out = len(A), len(B), []
while i and j:
    if A[i - 1] == B[j - 1]:
        out.append(A[i - 1]); i -= 1; j -= 1
    elif dp[i - 1][j] >= dp[i][j - 1]:
        i -= 1
    else:
        j -= 1
print("LCS 长度:", dp[-1][-1], "| 序列:", "".join(reversed(out)))
