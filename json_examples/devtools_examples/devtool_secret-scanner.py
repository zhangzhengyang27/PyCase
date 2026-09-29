"""泄漏扫描：密钥/密码/AK-SK 正则排查。"""
import argparse
import re
from pathlib import Path

RULES = [
    ("AWS AK", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("私钥块", re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----")),
    ("通用密码", re.compile(r"""(?i)(password|passwd|pwd)\s*[=:（(]\s*['\"]?[^\s'\"()（）]{6,}""")),
    ("Bearer token", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}")),
    ("国内云 AK", re.compile(r"(?:LTAI|AKID)[A-Za-z0-9]{12,}")),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    hits = 0
    for p in Path(args.directory).rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".md", ".env", ".sh"}:
            continue
        if any(x in p.parts for x in ("node_modules", ".git")):
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for name, rx in RULES:
                if rx.search(line):
                    hits += 1
                    print(f"⚠ {p}:{i} [{name}] {line.strip()[:70]}")
    print(f"扫描完成，{hits} 处可疑")


if __name__ == "__main__":
    main()
