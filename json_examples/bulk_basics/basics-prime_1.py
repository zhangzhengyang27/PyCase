"""素数筛：找出 100 以内的全部素数并统计。"""
limit = 100
sieve = [True] * (limit + 1)
sieve[0] = sieve[1] = False
for n in range(2, int(limit ** 0.5) + 1):
    if sieve[n]:
        for m in range(n * n, limit + 1, n):
            sieve[m] = False
primes = [i for i, ok in enumerate(sieve) if ok]
print(f"100 以内素数 {{len(primes)}} 个：", primes[:20], "...")
