"""限速器：装饰器实现最小间隔。"""
import functools
import time

def rate_limit(min_interval):
    last = [0.0]
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = min_interval - (time.monotonic() - last[0])
            if wait > 0:
                time.sleep(wait)
            last[0] = time.monotonic()
            return func(*args, **kwargs)
        return wrapper
    return deco

@rate_limit(0.5)
def fetch(url):
    print("fetch", url, "@", time.strftime("%H:%M:%S"))
    return url

for i in range(4):
    fetch(f"https://example.com/item/{i}")
