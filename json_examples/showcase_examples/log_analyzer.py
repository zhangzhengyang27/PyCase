"""日志分析：等级统计 + 错误明细。"""
import re
from collections import Counter

SAMPLE = """2026-09-22 10:00:01 INFO 服务启动 port=8000
2026-09-22 10:00:03 DEBUG 缓存预热 128 项
2026-09-22 10:01:22 WARN 响应超时 3.2s /api/list
2026-09-22 10:02:45 ERROR 数据库连接失败 retry=1
2026-09-22 10:03:10 INFO 请求 /health 200
2026-09-22 10:04:01 ERROR 数据库连接失败 retry=2
2026-09-22 10:05:33 WARN 慢查询 1.8s
"""

pattern = re.compile(r"^(?P<time>[\d-]+ [\d:]+) (?P<level>[A-Z]+) (?P<msg>.+)$")
counter = Counter()
errors = []

for line in SAMPLE.strip().splitlines():
    m = pattern.match(line)
    if not m:
        continue
    counter[m["level"]] += 1
    if m["level"] == "ERROR":
        errors.append((m["time"], m["msg"]))

print("等级分布:", dict(counter))
print("错误明细:")
for t, msg in errors:
    print(f"  {t}  {msg}")
