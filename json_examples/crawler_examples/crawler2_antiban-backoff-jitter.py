"""退避抖动：base * 2^n + jitter。"""
import random
import time

def backoff(attempt, base=0.5, cap=8.0):
    return min(cap, base * 2 ** attempt) + random.uniform(0, 0.3)

for n in range(5):
    print(f"第 {n} 次重试等待 {backoff(n):.2f}s")
    time.sleep(0.05)  # 演示用缩短
