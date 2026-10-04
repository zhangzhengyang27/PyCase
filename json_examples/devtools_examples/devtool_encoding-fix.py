"""编码修复：GBK/Latin1 → UTF-8 批量转换。"""
import argparse
from pathlib import Path


def decode_flexible(data: bytes):
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return data.decode(enc), enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--ext", nargs="*", default=[".txt", ".csv", ".md"])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # 自播种：默认扫描当前目录且没有候选文件时，先生成演示数据再继续（含一个 GBK 编码文件）
    if args.directory == ".":
        if not any(p.suffix in args.ext and p.is_file() for p in Path(".").rglob("*")):
            (Path(".") / "demo_utf8.txt").write_text("这是 UTF-8 演示文本\n第二行\n", encoding="utf-8")
            (Path(".") / "demo_gbk.txt").write_text("这是 GBK 编码的演示文本\n", encoding="gbk")
            print("未发现候选文件，已生成演示数据：demo_utf8.txt / demo_gbk.txt")

    for p in Path(args.directory).rglob("*"):
        if p.suffix not in args.ext or not p.is_file():
            continue
        text, enc = decode_flexible(p.read_bytes())
        if text is None:
            print("无法识别:", p)
        elif enc != "utf-8":
            print(f"{p}: {enc} -> utf-8")
            if args.apply:
                p.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
