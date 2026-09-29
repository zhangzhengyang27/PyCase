"""矩阵乘法：4×4 方阵（纯 Python 验证）。"""
A = [[(i * j + 1) % 7 for j in range(4)] for i in range(4)]
B = [[(i + 2 * j) % 7 for j in range(4)] for i in range(4)]
C = [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
print("C[0][:6] =", C[0][:6])
print("C[-1][-3:] =", C[-1][-3:])
