"""斐波那契第 80 项：三种实现对照。"""
from functools import lru_cache


@lru_cache(maxsize=None)
def fib_rec(k):
    return k if k < 2 else fib_rec(k - 1) + fib_rec(k - 2)


def fib_iter(k):
    a, b = 0, 1
    for _ in range(k):
        a, b = b, a + b
    return a


def fib_fast(k):
    def mul(x, y):
        return [[x[0][0] * y[0][0] + x[0][1] * y[1][0], x[0][0] * y[0][1] + x[0][1] * y[1][1]],
                [x[1][0] * y[0][0] + x[1][1] * y[1][0], x[1][0] * y[0][1] + x[1][1] * y[1][1]]]

    def mpow(m, e):
        r = [[1, 0], [0, 1]]
        while e:
            if e & 1:
                r = mul(r, m)
            m = mul(m, m)
            e >>= 1
        return r

    return mpow([[1, 1], [1, 0]], k)[0][1]


n = 80
print("迭代:", fib_iter(n), "| 递归:", fib_rec(n), "| 快速幂:", fib_fast(n))
