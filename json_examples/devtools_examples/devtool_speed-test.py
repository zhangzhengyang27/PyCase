"""网速测试：下载 1MB×3 次取均值。"""
import time
import requests

sizes = []
for i in range(3):
    t0 = time.monotonic()
    data = requests.get("https://httpbin.org/bytes/1048576", timeout=30).content
    secs = time.monotonic() - t0
    sizes.append(len(data) / secs / 1024 / 1024)
    print(f"第{i + 1}次: {sizes[-1]:.2f} MB/s")
print(f"平均: {sum(sizes) / len(sizes):.2f} MB/s")
