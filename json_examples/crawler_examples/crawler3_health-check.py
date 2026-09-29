"""健康检查：多目标探测与报告。"""
import time
import requests

TARGETS = [
    ("httpbin", "https://httpbin.org/status/200"),
    ("jsonplaceholder", "https://jsonplaceholder.typicode.com/posts/1"),
    ("github", "https://api.github.com"),
]
report = []
for name, url in TARGETS:
    t0 = time.monotonic()
    try:
        code = requests.get(url, timeout=8).status_code
        ok = code < 400
    except requests.RequestException:
        code, ok = 0, False
    report.append((name, code, (time.monotonic() - t0) * 1000, ok))
for name, code, ms, ok in report:
    print(f"{'✓' if ok else '✗'} {name:<16} {code or '-':>3}  {ms:6.0f}ms")
