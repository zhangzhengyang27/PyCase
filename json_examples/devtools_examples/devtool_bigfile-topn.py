"""大文件 TopN：python devtool_bigfile.py <目录> [--top 10]"""
import argparse
from pathlib import Path

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


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def main():
    ap = argparse.ArgumentParser(description="递归查找最大的 N 个文件")
    ap.add_argument("directory", nargs="?", default="演示数据")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()


    files = [(f.stat().st_size, f) for f in Path(args.directory).rglob("*") if f.is_file()]
    files.sort(reverse=True)
    for size, p in files[: args.top]:
        print(f"{human(size):>10}  {p}")


if __name__ == "__main__":
    main()
