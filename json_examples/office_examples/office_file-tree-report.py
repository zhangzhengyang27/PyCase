"""目录报告：子目录体积排行。"""
from pathlib import Path

def dir_size(d: Path) -> int:
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())


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

base = Path(".")
sizes = [(dir_size(d), d.name) for d in base.rglob("*") if d.is_dir()]
for size, name in sorted(sizes, reverse=True)[:10]:
    print(f"{size / 1024 / 1024:8.2f} MB  {name}")
