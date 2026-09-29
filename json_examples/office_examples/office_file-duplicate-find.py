"""重复文件：按内容哈希分组。"""
import hashlib
from pathlib import Path
from collections import defaultdict

groups = defaultdict(list)
for p in Path(".").iterdir():
    if p.is_file() and p.stat().st_size < 1024 * 1024:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        groups[h].append(p)

for h, paths in groups.items():
    if len(paths) > 1:
        print("重复组:", [str(p) for p in paths])
print("扫描完成")
