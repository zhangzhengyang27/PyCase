"""装饰器实战：计时 + 重试。"""
import functools
import time
import random


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        cost = (time.perf_counter() - start) * 1000
        print(f"[timer] {func.__name__} 耗时 {cost:.2f}ms")
        return result
    return wrapper


def retry(times=3, delay=0.1):
    """失败自动重试的参数化装饰器。"""
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"[retry] 第 {attempt} 次失败: {e}")
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return deco


@timer
def slow_add(a, b):
    time.sleep(0.05)
    return a + b


@retry(times=4)
def flaky():
    """30% 概率失败，演示重试。"""
    if random.random() < 0.3:
        raise RuntimeError("随机故障")
    return "成功"


print(slow_add(1, 2))
print(flaky())
