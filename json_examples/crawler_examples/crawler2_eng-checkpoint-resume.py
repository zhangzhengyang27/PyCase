"""断点续抓：游标状态持久化。"""
import json
from pathlib import Path

STATE = Path("cursor.json")
cursor = json.loads(STATE.read_text())["cursor"] if STATE.exists() else 0
TOTAL = 10
print(f"从游标 {cursor} 继续")
for page in range(cursor, TOTAL):
    print(f"处理页 {page}")
    cursor = page + 1
    if page == 5:  # 模拟中断
        break
STATE.write_text(json.dumps({"cursor": cursor}))
print(f"游标已存至 {cursor}，重跑将继续")
