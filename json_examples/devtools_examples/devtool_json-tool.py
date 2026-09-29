"""JSON 工具：format | minify | check"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["format", "minify", "check"])
    ap.add_argument("file")
    args = ap.parse_args()
    src = Path(args.file)
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"JSON 非法: {e}")
        raise SystemExit(1)
    if args.mode == "check":
        print("JSON 合法，顶层类型:", type(data).__name__)
    elif args.mode == "format":
        src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("已格式化 ->", src)
    else:
        src.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("已压缩 ->", src)


if __name__ == "__main__":
    main()
