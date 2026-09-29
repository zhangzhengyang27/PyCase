"""生成器：惰性序列。"""
import itertools


def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def primes(limit):
    """埃拉托斯特尼筛法的生成器版本。"""
    sieve = [True] * (limit + 1)
    for n in range(2, limit + 1):
        if sieve[n]:
            yield n
            for m in range(n * n, limit + 1, n):
                sieve[m] = False


# 取前 10 个斐波那契数（无限序列只按需计算）
fib = itertools.islice(fibonacci(), 10)
print("斐波那契:", list(fib))

print("100 以内素数:", list(primes(100)))

# 生成器表达式与 sum/all 组合
squares = (n * n for n in range(10))
print("平方和:", sum(squares))
print("全为正:", all(x > 0 for x in [1, 2, 3]))
