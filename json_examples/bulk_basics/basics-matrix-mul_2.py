"""矩阵乘法：6×6 方阵（纯 Python 验证）。"""
A = [[(i * j + 1) % 11 for j in range(6)] for i in range(6)]
B = [[(i + 2 * j) % 11 for j in range(6)] for i in range(6)]
C = [[sum(A[i][k] * B[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
print("C[0][:6] =", C[0][:6])
print("C[-1][-3:] =", C[-1][-3:])
