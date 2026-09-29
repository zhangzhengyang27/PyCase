"""分域限速：每个域名独立的最小间隔。"""
import time
from collections import defaultdict
from urllib.parse import urlparse

_last = defaultdict(float)
INTERVALS = {"api.github.com": 2.0, "httpbin.org": 0.5}

def throttled(url, fn):
    host = urlparse(url).netloc
    wait = INTERVALS.get(host, 1.0) - (time.monotonic() - _last[host])
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()
    return fn(url)

for u in ["https://httpbin.org/get?a=1", "https://httpbin.org/get?a=2",
          "https://api.github.com/zen"]:
    print("调度:", urlparse(u).netloc)
    throttled(u, lambda x: None)
