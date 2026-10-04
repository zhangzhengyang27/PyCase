"""文件分类：图片/文档/压缩包/其他 四类归档。"""
import shutil
from pathlib import Path

RULES = {
    "图片": {".jpg", ".png", ".gif", ".webp"},
    "文档": {".docx", ".pdf", ".md", ".txt", ".xlsx"},
    "压缩包": {".zip", ".7z"},
}
base = Path("演示数据")

# ---- 空目录自播种：生成演示文件树，让示例零输入可运行 ----
from pathlib import Path as _P

_DEMO = _P("演示数据")
if not _DEMO.exists():
    _files = {
        "演示数据/文档/需求说明.md": "# 需求说明\n批量整理演示。",
        "演示数据/文档/会议记录.txt": "1. 排期确认\n2. 责任到人",
        "演示数据/图片/banner.png": "",
        "演示数据/图片/icon.png": "",
        "演示数据/导出/汇总.csv": "项目,数量\nA,3\nB,7\n",
        "演示数据/日志/run.log": "INFO start\nINFO done",
    }
    for rel, content in _files.items():
        _f = _P(rel)
        _f.parent.mkdir(parents=True, exist_ok=True)
        _f.write_bytes(content.encode("utf-8"))
    (_P("演示数据/图片/banner.png")).write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    (_P("演示数据/图片/icon.png")).write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 32)
    print("未指定目录：已自动生成演示文件树 演示数据/")
# ---- 自播种结束 ----

for p in list(base.rglob("*")):
    if not p.is_file():
        continue
    folder = next((name for name, exts in RULES.items() if p.suffix in exts), "其他")
    dest = base / folder
    dest.mkdir(exist_ok=True)
    shutil.move(str(p), dest / p.name)
    print(f"{p.name} -> {folder}/")
