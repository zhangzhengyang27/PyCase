"""pathlib：现代文件路径操作。"""
from pathlib import Path
import tempfile

base = Path(tempfile.mkdtemp(prefix="pathlib_demo_"))
(base / "docs").mkdir()
(base / "logs").mkdir()
(base / "docs" / "a.txt").write_text("hello", encoding="utf-8")
(base / "docs" / "b.md").write_text("# hi", encoding="utf-8")
(base / "logs" / "run.log").write_text("INFO ok", encoding="utf-8")

# glob 遍历
print("全部文件:", sorted(p.name for p in base.rglob("*") if p.is_file()))
print("markdown:", [p.name for p in base.rglob("*.md")])

# 读写与属性
doc = base / "docs" / "a.txt"
print("内容:", doc.read_text(encoding="utf-8"), "| 大小:", doc.stat().st_size)

# 重命名 + 目录树
doc.rename(doc.with_name("renamed.txt"))
for p in sorted(base.rglob("*")):
    print("  " * (len(p.relative_to(base).parts) - 1), p.name)
