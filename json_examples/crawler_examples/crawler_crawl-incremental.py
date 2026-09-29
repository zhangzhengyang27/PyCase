"""增量抓取：内容指纹去重，只处理新条目。"""
import hashlib
import json
from pathlib import Path

STATE = Path("crawl_state.json")
seen = json.loads(STATE.read_text()) if STATE.exists() else {}

feed = [{"id": i, "title": f"文章{i}", "body": f"内容{i}" + ("更新" if i == 3 else "")}
        for i in range(1, 8)]
new_count = 0
for item in feed:
    fp = hashlib.md5((str(item["id"]) + item["body"]).encode()).hexdigest()
    if seen.get(str(item["id"])) == fp:
        continue  # 未更新
    seen[str(item["id"])] = fp
    new_count += 1
    print("新/更新:", item["title"])
STATE.write_text(json.dumps(seen, ensure_ascii=False, indent=1))
print(f"本次新增/更新 {new_count} 条")
