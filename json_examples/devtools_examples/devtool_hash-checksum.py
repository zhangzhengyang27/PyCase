"""哈希校验：文件多算法指纹。"""
import argparse
import hashlib
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--algo", nargs="*", default=["md5", "sha1", "sha256"])
    args = ap.parse_args()
    data = Path(args.file).read_bytes()
    for algo in args.algo:
        h = hashlib.new(algo, data).hexdigest()
        print(f"{algo:<8} {h}  {Path(args.file).name}")


if __name__ == "__main__":
    main()
