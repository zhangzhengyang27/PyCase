"""压缩/解压：zip 与 tar.gz 统一接口。"""
import argparse
import tarfile
import zipfile
from pathlib import Path


def pack(folder, out):
    if out.suffix == ".zip":
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in Path(folder).rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(folder))
    else:
        with tarfile.open(out, "w:gz") as tf:
            tf.add(folder, arcname=Path(folder).name)


def unpack(archive, dest):
    dest = Path(dest)
    dest.mkdir(exist_ok=True)
    if archive.suffix == ".zip":
        zipfile.ZipFile(archive).extractall(dest)
    else:
        tarfile.open(archive).extractall(dest)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p1 = sub.add_parser("pack"); p1.add_argument("folder"); p1.add_argument("out")
    p2 = sub.add_parser("unpack"); p2.add_argument("archive"); p2.add_argument("dest")
    args = ap.parse_args()
    if args.mode == "pack":
        pack(args.folder, args.out); print("已压缩 ->", args.out)
    else:
        unpack(args.archive, args.dest); print("已解压 ->", args.dest)


if __name__ == "__main__":
    main()
