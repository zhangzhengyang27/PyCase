""".env 校验：缺失键与多余键清单。"""
import argparse
from pathlib import Path


def load_keys(path):
    if not Path(path).exists():
        return {}
    keys = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            keys[k] = v
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=".env")
    ap.add_argument("--example", default=".env.example")
    args = ap.parse_args()
    env, example = load_keys(args.env), load_keys(args.example)
    missing = [k for k in example if k not in env]
    extra = [k for k in env if k not in example]
    empty = [k for k, v in env.items() if not v]
    if missing: print("缺失键:", missing)
    if extra: print("多余键:", extra)
    if empty: print("空值键:", empty)
    if not (missing or extra or empty): print(".env 与 example 一致")


if __name__ == "__main__":
    main()
