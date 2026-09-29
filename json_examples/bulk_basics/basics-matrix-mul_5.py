"""矩阵乘法：12×12 方阵（纯 Python 验证）。"""
A = [[(i * j + 1) % 9 for j in range(12)] for i in range(12)]
B = [[(i + 2 * j) % 9 for j in range(12)] for i in range(12)]
C = [[sum(A[i][k] * B[k][j] for k in range(12)) for j in range(12)] for i in range(12)]
print("C[0][:6] =", C[0][:6])
print("C[-1][-3:] =", C[-1][-3:])
