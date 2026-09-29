"""JSONL：流式抓取的标准落盘格式。"""
import json
from pathlib import Path

dest = Path("crawl_result.jsonl")
with dest.open("a", encoding="utf-8") as f:
    for i in range(5):
        record = {"id": i, "title": f"条目{i}", "ts": "2026-09-23T10:00:00"}
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
print("追加 5 行 ->", dest)
print("当前行数:", sum(1 for _ in dest.open(encoding="utf-8")))
