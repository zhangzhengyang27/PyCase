"""矩阵乘法：10×10 方阵（纯 Python 验证）。"""
A = [[(i * j + 1) % 5 for j in range(10)] for i in range(10)]
B = [[(i + 2 * j) % 5 for j in range(10)] for i in range(10)]
C = [[sum(A[i][k] * B[k][j] for k in range(10)) for j in range(10)] for i in range(10)]
print("C[0][:6] =", C[0][:6])
print("C[-1][-3:] =", C[-1][-3:])
