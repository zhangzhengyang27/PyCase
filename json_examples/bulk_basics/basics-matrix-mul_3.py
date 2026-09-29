"""矩阵乘法：8×8 方阵（纯 Python 验证）。"""
A = [[(i * j + 1) % 13 for j in range(8)] for i in range(8)]
B = [[(i + 2 * j) % 13 for j in range(8)] for i in range(8)]
C = [[sum(A[i][k] * B[k][j] for k in range(8)) for j in range(8)] for i in range(8)]
print("C[0][:6] =", C[0][:6])
print("C[-1][-3:] =", C[-1][-3:])
