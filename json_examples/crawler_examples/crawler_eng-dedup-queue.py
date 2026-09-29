"""URL 队列：待抓/已抓去重 + 深度限制。"""
from collections import deque

start = "https://example.com/"
queue = deque([(start, 0)])
seen = {start}
results = []
MAX_DEPTH = 2

def fake_links(url):
    return [f"{url}/page{i}" for i in range(2)]

while queue:
    url, depth = queue.popleft()
    results.append((url, depth))
    if depth >= MAX_DEPTH:
        continue
    for link in fake_links(url):
        if link not in seen:
            seen.add(link)
            queue.append((link, depth + 1))

print(f"共发现 {len(results)} 个 URL，最大深度 {max(d for _, d in results)}")
for u, d in results[:6]:
    print("  " * d, u[-20:])
