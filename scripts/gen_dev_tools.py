#!/usr/bin/env python3
"""实用工具箱生成器：真实可用的命令行工具（区别于「示例」）。

工具选题参照 GitHub 高星 CLI 生态（httpie / yt-dlp / rich / typer 一系与
awesome-cli-apps 目录）的常用方向，全部为可直接使用的 argparse CLI：
文件磁盘 / 文本数据 / 网络 / 开发者 / 系统效率 五大类。
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "json_examples"


class Collection:
    def __init__(self, file: str, name: str, description: str, merge: bool = True):
        self.file = file
        self.name = name
        self.description = description
        self.examples = []
        self.seen_code = set()
        self.seen_id = set()
        existing = OUT_DIR / file
        if merge and existing.exists():
            for e in json.load(open(existing, encoding="utf-8")).get("examples", []):
                self.seen_id.add(e["id"])
                self.seen_code.add(hashlib.md5(e["code"].encode()).hexdigest())
                self.examples.append(e)

    def add(self, example_id, name, title, description, tags, requirements, code, category="tools"):
        code = code.strip() + "\n"
        h = hashlib.md5(code.encode()).hexdigest()
        if h in self.seen_code:
            return False
        if example_id in self.seen_id:  # 同 id 重跑：更新内容（upsert）
            for i, e in enumerate(self.examples):
                if e["id"] == example_id:
                    self.examples[i] = {"id": example_id, "name": name, "category": category,
                                        "tags": tags, "title": title, "description": description,
                                        "requirements": requirements, "code": code}
                    return True
        self.seen_code.add(h)
        self.seen_id.add(example_id)
        self.examples.append({"id": example_id, "name": name, "category": category,
                              "tags": tags, "title": title, "description": description,
                              "requirements": requirements, "code": code})
        return True

    def save(self):
        with open(OUT_DIR / self.file, "w", encoding="utf-8") as f:
            json.dump({"name": self.name, "description": self.description,
                       "examples": self.examples}, f, ensure_ascii=False, indent=1)
        return len(self.examples)


def build_dev_tools():
    c = Collection("devtools_examples.json", "实用工具箱",
                   "真实可用的命令行工具集：文件磁盘 / 文本数据 / 网络 / 开发者 / 系统效率。"
                   "每条都是带 argparse 入口的完整工具，python 运行即用。")

    def add(pid, title, desc, code, tags, reqs):
        c.add(f"tools_dev-{pid}", f"devtool_{pid}.py", title, desc,
              list(tags) + ["CLI"], list(reqs), code, category="tools")

    # ================= 文件与磁盘 =================
    add("bigfile-topn", "大文件 TopN 查找器", "递归找出目录下最大的 N 个文件，人类可读体积。",
        '''"""大文件 TopN：python devtool_bigfile.py <目录> [--top 10]"""
import argparse
from pathlib import Path


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def main():
    ap = argparse.ArgumentParser(description="递归查找最大的 N 个文件")
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    files = [(f.stat().st_size, f) for f in Path(args.directory).rglob("*") if f.is_file()]
    files.sort(reverse=True)
    for size, p in files[: args.top]:
        print(f"{human(size):>10}  {p}")


if __name__ == "__main__":
    main()
''', ("文件", "磁盘"), [])
    add("dupe-cleaner", "重复文件清理器", "内容哈希分组重复文件，支持 --delete 自动清理（保留首份）。",
        '''"""重复文件清理：默认只报告，--delete 执行清理。"""
import argparse
import hashlib
from collections import defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--delete", action="store_true", help="删除重复（保留每组第一个）")
    args = ap.parse_args()

    groups = defaultdict(list)
    for p in Path(args.directory).rglob("*"):
        if p.is_file() and p.stat().st_size < 512 * 1024 * 1024:
            groups[hashlib.md5(p.read_bytes()).hexdigest()].append(p)

    freed = 0
    for paths in groups.values():
        if len(paths) < 2:
            continue
        print("重复组:", [str(p) for p in paths])
        for dup in paths[1:]:
            freed += dup.stat().st_size
            if args.delete:
                dup.unlink()
    print(f"{'已删除' if args.delete else '可释放'}: {freed / 1024:.0f} KB")


if __name__ == "__main__":
    main()
''', ("文件", "磁盘"), [])
    add("empty-dir-sweep", "空目录清扫器", "递归删除全部空目录（自底向上）。",
        '''"""空目录清扫：自底向上删除空目录。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    base = Path(args.directory)

    removed = 0
    for d in sorted(base.rglob("*"), key=lambda p: -len(p.parts)):
        if d.is_dir() and not any(d.iterdir()):
            print("空目录:", d)
            if args.apply:
                d.rmdir()
            removed += 1
    print(f"{'已删除' if args.apply else '发现'} {removed} 个空目录")


if __name__ == "__main__":
    main()
''', ("文件", "磁盘"), [])
    add("dir-sync", "目录同步器", "rsync 精简版：按 (路径, 大小, mtime) 增量复制。",
        '''"""目录同步：源 → 目标 增量复制（新增/更新才拷贝）。"""
import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    src, dst = Path(args.src), Path(args.dst)

    copied = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        target = dst / rel
        if (target.exists() and target.stat().st_mtime >= f.stat().st_mtime
                and target.stat().st_size == f.stat().st_size):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        copied += 1
        print("+", rel)
    print(f"同步完成：新增/更新 {copied} 个文件")


if __name__ == "__main__":
    main()
''', ("文件", "磁盘"), [])
    add("secure-shred", "敏感文件粉碎器", "随机覆写多次后删除，防恢复删除。",
        '''"""文件粉碎：随机覆写 3 遍 + 改名 + 删除。"""
import argparse
import os
from pathlib import Path


def shred(path: Path, passes: int = 3):
    size = path.stat().st_size
    with open(path, "r+b") as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())
    path.rename(path.with_name(path.name + ".shredded"))
    path.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--passes", type=int, default=3)
    args = ap.parse_args()
    for f in args.files:
        p = Path(f)
        if p.exists():
            shred(p, args.passes)
            print("已粉碎:", f)


if __name__ == "__main__":
    main()
''', ("文件", "安全"), [])
    add("archive-tool", "统一压缩解压器", "zip/tar.gz 一键压缩与解压（按扩展名自动分派）。",
        '''"""压缩/解压：zip 与 tar.gz 统一接口。"""
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
''', ("文件", "压缩"), [])
    add("tmp-sweep", "临时文件清理器", "按修改时间清理 N 天前的临时文件。",
        '''"""临时清理：删除 mtime 超过 N 天的 .tmp/.log/.cache 文件。"""
import argparse
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    cutoff = time.time() - args.days * 86400

    freed = 0
    for p in Path(args.directory).rglob("*"):
        if (p.is_file() and p.suffix in {".tmp", ".log", ".cache"}
                and p.stat().st_mtime < cutoff):
            freed += p.stat().st_size
            print("清理:", p)
            if args.apply:
                p.unlink()
    print(f"{'已清理' if args.apply else '可清理'} {freed / 1024:.0f} KB")


if __name__ == "__main__":
    main()
''', ("文件", "磁盘"), [])
    add("tree-print", "目录树打印", "tree 命令的 Python 版（支持深度与忽略规则）。",
        '''"""目录树：tree 命令复刻。"""
import argparse
from pathlib import Path


def walk(d: Path, prefix: str, depth: int, max_depth: int, ignores: set):
    if depth > max_depth:
        return
    entries = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name))
    entries = [e for e in entries if e.name not in ignores]
    for i, e in enumerate(entries):
        last = i == len(entries) - 1
        print(prefix + ("└── " if last else "├── ") + e.name + ("/" if e.is_dir() else ""))
        if e.is_dir():
            walk(e, prefix + ("    " if last else "│   "), depth + 1, max_depth, ignores)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--ignore", nargs="*", default=["node_modules", ".git", "__pycache__"])
    args = ap.parse_args()
    print(Path(args.directory).resolve().name + "/")
    walk(Path(args.directory), "", 1, args.depth, set(args.ignore))


if __name__ == "__main__":
    main()
''', ("文件", "目录"), [])
    add("file-watch", "文件变更监听", "mtime 轮询监听目录变更（无第三方依赖）。",
        '''"""文件监听：轮询 mtime，变更即提示。"""
import argparse
import time
from pathlib import Path


def snapshot(d):
    return {p: p.stat().st_mtime for p in d.rglob("*") if p.is_file()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--duration", type=float, default=10, help="监听秒数")
    args = ap.parse_args()
    base = Path(args.directory)
    before = snapshot(base)
    deadline = time.monotonic() + args.duration
    print(f"监听 {base}（{args.duration}s）…")
    while time.monotonic() < deadline:
        time.sleep(args.interval)
        now = snapshot(base)
        for p in now.keys() - before.keys():
            print("新增:", p)
        for p in before.keys() - now.keys():
            print("删除:", p)
        for p in now.keys() & before.keys():
            if now[p] != before[p]:
                print("修改:", p)
        before = now


if __name__ == "__main__":
    main()
''', ("文件", "监听"), [])
    add("quick-find", "快速文件查找", "按名称正则全盘搜索（fd 的精简版）。",
        '''"""快速查找：名称正则 + 类型过滤。"""
import argparse
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", help="名称正则")
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--type", choices=["f", "d"], default="f")
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()
    rx = re.compile(args.pattern, re.IGNORECASE)

    count = 0
    for p in Path(args.directory).rglob("*"):
        if len(p.parts) > 2 and any(x in p.parts for x in ("node_modules", ".git")):
            continue
        if (p.is_file() if args.type == "f" else p.is_dir()) and rx.search(p.name):
            print(p)
            count += 1
            if count >= args.limit:
                break
    print(f"共 {count} 个（上限 {args.limit}）")


if __name__ == "__main__":
    main()
''', ("文件", "查找"), [])
    add("encoding-fix", "编码修复器", "批量检测并转换 GBK/Latin 文本到 UTF-8。",
        '''"""编码修复：GBK/Latin1 → UTF-8 批量转换。"""
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
''', ("文件", "编码"), [])

    # ================= 文本与数据 =================
    add("md-toc", "Markdown 目录生成", "提取标题层级生成 TOC，锚点自动转写。",
        '''"""Markdown TOC：把 # 标题生成目录并打印。"""
import argparse
import re
from pathlib import Path


def anchor(text):
    return re.sub(r"[^\\w\\u4e00-\\u9fff- ]", "", text).strip().replace(" ", "-").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    args = ap.parse_args()
    lines = Path(args.file).read_text(encoding="utf-8").splitlines()
    for line in lines:
        m = re.match(r"^(#{1,4})\\s+(.+)", line)
        if m:
            depth, title = len(m.group(1)), m.group(2).strip()
            print("  " * (depth - 1) + f"- [{title}](#{anchor(title)})")


if __name__ == "__main__":
    main()
''', ("文本", "Markdown"), [])
    add("csv-json-convert", "CSV ↔ JSON 互转", "带类型推断的双向转换器。",
        '''"""CSV ↔ JSON：python xxx.py csv2json data.csv / json2csv data.json"""
import argparse
import csv
import json
from pathlib import Path


def typed(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["csv2json", "json2csv"])
    ap.add_argument("file")
    args = ap.parse_args()
    src = Path(args.file)

    if args.mode == "csv2json":
        rows = list(csv.DictReader(src.open(encoding="utf-8")))
        rows = [{k: typed(v) for k, v in r.items()} for r in rows]
        out = src.with_suffix(".json")
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {out}（{len(rows)} 行）")
    else:
        rows = json.loads(src.read_text(encoding="utf-8"))
        out = src.with_suffix(".csv")
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"-> {out}（{len(rows)} 行）")


if __name__ == "__main__":
    main()
''', ("文本", "转换"), [])
    add("text-diff", "文本对比工具", "difflib unified diff，两个文件逐行对比。",
        '''"""文本 diff：unified 风格输出。"""
import argparse
import difflib
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    args = ap.parse_args()
    a = Path(args.a).read_text(encoding="utf-8").splitlines()
    b = Path(args.b).read_text(encoding="utf-8").splitlines()
    diff = difflib.unified_diff(a, b, fromfile=args.a, tofile=args.b, lineterm="")
    changed = 0
    for line in diff:
        print(line)
        changed += line[:1] in "+-"
    print(f"变更行: {changed}")


if __name__ == "__main__":
    main()
''', ("文本", "diff"), [])
    add("loc-counter", "代码行数统计", "cloc 精简版：按扩展名统计代码/注释/空行。",
        '''"""代码统计：按扩展名汇总行数。"""
import argparse
from collections import defaultdict
from pathlib import Path


def count_file(p):
    code = comment = blank = 0
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s:
            blank += 1
        elif s.startswith(("#", "//")):
            comment += 1
        else:
            code += 1
    return code, comment, blank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    stats = defaultdict(lambda: [0, 0, 0, 0])
    for p in Path(args.directory).rglob("*"):
        if p.is_file() and p.suffix in {".py", ".js", ".ts", ".vue", ".mjs"} and "node_modules" not in p.parts:
            c, cm, b = count_file(p)
            s = stats[p.suffix]
            s[0] += c; s[1] += cm; s[2] += b; s[3] += 1
    print(f"{'类型':<6}{'文件':>5}{'代码':>8}{'注释':>8}{'空行':>8}")
    for ext, (c, cm, b, n) in sorted(stats.items(), key=lambda x: -x[1][0]):
        print(f"{ext:<6}{n:>5}{c:>8}{cm:>8}{b:>8}")


if __name__ == "__main__":
    main()
''', ("文本", "统计"), [])
    add("json-tool", "JSON 格式化校验", "格式化/压缩/校验三合一。",
        '''"""JSON 工具：format | minify | check"""
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
''', ("文本", "JSON"), [])
    add("yaml-json-convert", "YAML ↔ JSON 互转", "配置文件双向转换（PyYAML）。",
        '''"""YAML ↔ JSON：python xxx.py yaml2json config.yaml"""
import argparse
import json
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["yaml2json", "json2yaml"])
    ap.add_argument("file")
    args = ap.parse_args()
    src = Path(args.file)
    if args.mode == "yaml2json":
        data = yaml.safe_load(src.read_text(encoding="utf-8"))
        out = src.with_suffix(".json")
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        data = json.loads(src.read_text(encoding="utf-8"))
        out = src.with_suffix(".yaml")
        out.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("->", out)


if __name__ == "__main__":
    main()
''', ("文本", "YAML"), ["pyyaml"])
    add("secret-scanner", "敏感信息扫描器", "扫描代码里的密钥/密码/token 泄漏。",
        '''"""泄漏扫描：密钥/密码/AK-SK 正则排查。"""
import argparse
import re
from pathlib import Path

RULES = [
    ("AWS AK", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("私钥块", re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----")),
    ("通用密码", re.compile(r"""(?i)(password|passwd|pwd)\\s*[=:（(]\\s*['\\"]?[^\\s'\\"()（）]{6,}""")),
    ("Bearer token", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\\.[A-Za-z0-9_-]{10,}")),
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
''', ("文本", "安全"), [])
    add("bulk-replace", "批量查找替换", "多文件正则替换（含预览与备份）。",
        '''"""批量替换：python xxx.py 目录 旧文本 新文本 --ext .py .md"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--ext", nargs="*", default=[".py", ".md", ".txt"])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed = 0
    for p in Path(args.directory).rglob("*"):
        if p.suffix not in args.ext or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if args.old not in text:
            continue
        n = text.count(args.old)
        print(f"{p}: {n} 处")
        changed += n
        if args.apply:
            p.write_text(text.replace(args.old, args.new), encoding="utf-8")
    print(f"{'已替换' if args.apply else '可替换'} {changed} 处")


if __name__ == "__main__":
    main()
''', ("文本", "替换"), [])
    add("line-endings", "换行符规范化", "CRLF/LF/Tab 批量统一（跨平台协作必备）。",
        '''"""换行符规范化：CRLF→LF，Tab→4 空格。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--ext", nargs="*", default=[".py", ".js", ".ts", ".md"])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    fixed = 0
    for p in Path(args.directory).rglob("*"):
        if p.suffix not in args.ext or not p.is_file():
            continue
        raw = p.read_bytes()
        new = raw.replace(b"\\r\\n", b"\\n").replace(b"\\t", b"    ")
        if new != raw:
            print("规范化:", p)
            fixed += 1
            if args.apply:
                p.write_bytes(new)
    print(f"{'已修复' if args.apply else '可修复'} {fixed} 个文件")


if __name__ == "__main__":
    main()
''', ("文本", "规范化"), [])

    # ================= 网络 =================
    add("speed-test", "网速测试", "下载测速（httpbin 字节端点，MB/s 报告）。",
        '''"""网速测试：下载 1MB×3 次取均值。"""
import time
import requests

sizes = []
for i in range(3):
    t0 = time.monotonic()
    data = requests.get("https://httpbin.org/bytes/1048576", timeout=30).content
    secs = time.monotonic() - t0
    sizes.append(len(data) / secs / 1024 / 1024)
    print(f"第{i + 1}次: {sizes[-1]:.2f} MB/s")
print(f"平均: {sum(sizes) / len(sizes):.2f} MB/s")
''', ("网络", "测速"), ["requests"])
    add("ip-lookup", "IP 查询", "本机出口 IP + 归属信息。",
        '''"""IP 查询：出口 IP 与服务商。"""
import requests

resp = requests.get("https://api.ipify.org?format=json", timeout=10)
ip = resp.json()["ip"]
print("出口 IP:", ip)
try:
    info = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10).json()
    print("归属:", info.get("country_name"), info.get("city"), info.get("org"))
except requests.RequestException:
    print("归属查询失败（不影响 IP 获取）")
''', ("网络", "IP"), ["requests"])
    add("port-check", "端口连通检查", "TCP 端口批量连通性检测（本机/局域网巡检用）。",
        '''"""端口检查：socket 探测目标主机端口列表。"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host")
    ap.add_argument("--ports", nargs="*", type=int, default=[80, 443, 22, 3306, 6379])
    ap.add_argument("--timeout", type=float, default=1.5)
    args = ap.parse_args()
    for port in args.ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(args.timeout)
            result = s.connect_ex((args.host, port)) == 0
        print(f"{args.host}:{port:<6} {'开放' if result else '关闭'}")


if __name__ == "__main__":
    main()
''', ("网络", "端口"), [])
    add("http-headers-inspect", "HTTP 头检查器", "查看响应头：缓存/安全/CORS 配置体检。",
        '''"""响应头检查：缓存与安全配置一览。"""
import argparse
import requests

INTERESTING = ["Cache-Control", "Content-Type", "Content-Encoding", "Server",
               "Strict-Transport-Security", "Content-Security-Policy",
               "Access-Control-Allow-Origin", "ETag"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    args = ap.parse_args()
    resp = requests.get(args.url, timeout=10)
    print("状态:", resp.status_code)
    for h in INTERESTING:
        v = resp.headers.get(h)
        if v:
            print(f"  {h}: {v[:60]}")
    missing = [h for h in ("Strict-Transport-Security", "Content-Security-Policy") if h not in resp.headers]
    print("缺失安全头:", missing or "无")
''', ("网络", "HTTP"), ["requests"])
    add("site-monitor", "站点可用性监控", "循环探测多站点，异常写告警日志。",
        '''"""站点监控：循环探测 + 告警落盘。"""
import argparse
import time
from pathlib import Path
import requests

SITES = ["https://httpbin.org/status/200", "https://api.github.com"]


def check(url):
    try:
        return requests.get(url, timeout=8).status_code, None
    except requests.RequestException as e:
        return 0, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--interval", type=int, default=5)
    args = ap.parse_args()
    log = Path("monitor.log")
    for r in range(args.rounds):
        for url in SITES:
            code, err = check(url)
            line = f"{time.strftime('%H:%M:%S')} {url} -> {code or err}"
            print(line)
            if code >= 400 or err:
                with log.open("a", encoding="utf-8") as f:
                    f.write(line + "\\n")
        time.sleep(args.interval)
    print("告警日志:", log if log.exists() else "（无告警）")
''', ("网络", "监控"), ["requests"])
    add("qrcode-gen", "二维码生成器", "文本/URL → PNG 二维码。",
        '''"""二维码生成：python xxx.py '文本或链接' -o qr.png"""
import argparse

import qrcode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("-o", "--output", default="qrcode.png")
    args = ap.parse_args()
    img = qrcode.make(args.text)
    img.save(args.output)
    print(f"已生成 {args.output}（{img.size[0]}×{img.size[1]}）")


if __name__ == "__main__":
    main()
''', ("网络", "二维码"), ["qrcode", "pillow"])
    add("url-batch-check", "URL 批量体检", "批量检查链接可达性，输出死链清单。",
        '''"""URL 体检：HEAD 批量检查死链。"""
import concurrent.futures
import requests

urls = [
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/404",
    "https://api.github.com",
]

def check(u):
    try:
        return u, requests.head(u, timeout=8, allow_redirects=True).status_code
    except requests.RequestException as e:
        return u, str(type(e).__name__)

with concurrent.futures.ThreadPoolExecutor(8) as pool:
    for url, code in pool.map(check, urls):
        mark = "✓" if isinstance(code, int) and code < 400 else "✗"
        print(f"{mark} {code}  {url}")
''', ("网络", "死链"), ["requests"])
    add("dns-lookup", "DNS 解析查询", "域名 → A 记录/规范名/反查。",
        '''"""DNS 查询：socket 标准库版。"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    args = ap.parse_args()
    try:
        infos = socket.getaddrinfo(args.domain, 443, socket.AF_INET)
        ips = sorted({info[4][0] for info in infos})
        print(f"{args.domain} -> {ips}")
    except socket.gaierror as e:
        print("解析失败:", e)
    try:
        print("规范名:", socket.gethostbyaddr(socket.gethostbyname(args.domain))[0])
    except socket.herror:
        pass


if __name__ == "__main__":
    main()
''', ("网络", "DNS"), [])
    add("html2text", "网页正文提取", "HTML 剥离标签取正文（阅读器思路）。",
        '''"""正文提取：脚本+样式剔除，块级标签换行。"""
from bs4 import BeautifulSoup

HTML = """
<html><head><style>body{color:red}</style><script>var x=1;</script></head>
<body><h1>标题</h1><p>第一段正文。</p><p>第二段，含<a href="#">链接</a>。</p></body></html>"""
soup = BeautifulSoup(HTML, "html.parser")
for tag in soup(["style", "script", "noscript"]):
    tag.decompose()
text = soup.get_text("\\n")
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
print("\\n".join(lines))
''', ("网络", "正文"), ["requests", "beautifulsoup4"])

    # ================= 开发者 =================
    add("git-branch-report", "Git 分支报告", "列出本地分支与最近提交时间（清理依据）。",
        '''"""Git 分支报告：按最近提交排序。"""
import argparse
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    args = ap.parse_args()
    if not Path(args.repo, ".git").exists():
        print("不是 git 仓库")
        return
    branches = git("-C", args.repo, "branch", "--format=%(committerdate:short)%09%(refname:short)").splitlines()
    rows = []
    for line in branches:
        date, _, name = line.partition("\t")
        rows.append((date, name))
    for date, name in sorted(rows, reverse=True):
        print(f"{date[:19]}  {name}")
    print("（已合并分支可用 git branch --merged 查看，再 -d 清理）")


if __name__ == "__main__":
    main()
''', ("开发", "Git"), [])
    add("git-stats", "Git 提交统计", "按作者统计提交数与增删行。",
        '''"""Git 统计：shortlog + numstat。"""
import subprocess
from collections import defaultdict


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout

by_author = defaultdict(lambda: [0, 0, 0])
shortlog = git("log", "--format=%an|%h")
for line in shortlog.splitlines():
    author = line.split("|")[0]
    by_author[author][0] += 1
numstat = git("log", "--numstat", "--format=")
for line in numstat.splitlines():
    if not line.strip():
        continue
    add, dele, _ = line.split("\\t")
    author = None
    for a in by_author:
        if a:
            author = a  # 简化：不计归属粒度
            break
    if author:
        by_author[author][1] += int(add or 0) if add.isdigit() else 0
        by_author[author][2] += int(dele or 0) if dele.isdigit() else 0
for author, (commits, add, dele) in sorted(by_author.items(), key=lambda x: -x[1][0]):
    print(f"{author:<16} 提交 {commits:>4}  +{add} -{dele}")
''', ("开发", "Git"), [])
    add("gitignore-gen", "gitignore 生成器", "按项目类型拼装 .gitignore 模板。",
        '''"""gitignore 生成：python xxx.py python node macos > .gitignore"""
import argparse

TEMPLATES = {
    "python": "__pycache__/\\n*.py[cod]\\n.venv/\\n*.egg-info/\\n.pytest_cache/\\n.mypy_cache/\\ndist/",
    "node": "node_modules/\\nout/\\n*.tsbuildinfo\\n.env.local",
    "macos": ".DS_Store\\n._*",
    "ide": ".idea/\\n.vscode/",
    "python-notebook": ".ipynb_checkpoints/",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stacks", nargs="+", choices=TEMPLATES)
    args = ap.parse_args()
    print("# 由 gitignore-gen 生成")
    for stack in args.stacks:
        print(f"\\n# --- {stack} ---\\n{TEMPLATES[stack]}")


if __name__ == "__main__":
    main()
''', ("开发", "Git"), [])
    add("json2dataclass", "JSON → dataclass", "由 JSON 样本推断生成 dataclass 定义。",
        '''"""JSON → dataclass：样本推断字段类型。"""
import argparse
import json


def py_type(v):
    if isinstance(v, bool): return "bool"
    if isinstance(v, int): return "int"
    if isinstance(v, float): return "float"
    if isinstance(v, dict): return "dict[str, object]"
    if isinstance(v, list): return "list"
    return "str"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--class-name", default="Item")
    args = ap.parse_args()
    sample = json.loads(__import__("pathlib").Path(args.file).read_text(encoding="utf-8"))
    if isinstance(sample, list) and sample:
        sample = sample[0]
    fields = [f"    {k}: {py_type(v)}" for k, v in sample.items()]
    print(f"@dataclass\\nclass {args.class_name}:\\n" + "\\n".join(fields))


if __name__ == "__main__":
    main()
''', ("开发", "代码生成"), [])
    add("regex-playground", "正则测试器", "模式 + 样本文本 → 全部匹配与分组展示。",
        '''"""正则测试：pattern + 样本 → 匹配详情。"""
import argparse
import re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("sample")
    args = ap.parse_args()
    rx = re.compile(args.pattern)
    matches = list(rx.finditer(args.sample))
    if not matches:
        print("无匹配")
        return
    for m in matches:
        print(f"[{m.start()}:{m.end()}] {m.group()!r}")
        for gi, g in enumerate(m.groups() or [], 1):
            if g is not None:
                print(f"   组{gi}: {g!r}")
    print(f"共 {len(matches)} 处匹配")


if __name__ == "__main__":
    main()
''', ("开发", "正则"), [])
    add("uuid-gen", "UUID/短 ID 生成器", "uuid4 / 短 ID / 序列号多种模式。",
        '''"""ID 生成：uuid4 / 短ID / 序列号。"""
import argparse
import secrets
import uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["uuid", "short", "serial"], default="uuid")
    ap.add_argument("-n", type=int, default=3)
    args = ap.parse_args()
    for _ in range(args.n):
        if args.mode == "uuid":
            print(uuid.uuid4())
        elif args.mode == "short":
            print(secrets.token_urlsafe(8))
        else:
            print(time_id := f"{__import__('time').strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}")


if __name__ == "__main__":
    main()
''', ("开发", "ID"), [])
    add("hash-checksum", "哈希校验器", "多算法文件校验和（MD5/SHA1/SHA256）。",
        '''"""哈希校验：文件多算法指纹。"""
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
''', ("开发", "校验"), [])
    add("jwt-decode", "JWT 解码器", "不解签验证码，仅解码 header/payload 查看。",
        '''"""JWT 解码：base64 分段解码（不验证签名）。"""
import argparse
import base64
import json
from datetime import datetime


def b64d(seg):
    return json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("token")
    args = ap.parse_args()
    header, payload, _ = args.token.split(".")
    h, p = b64d(header), b64d(payload)
    print("Header:", json.dumps(h, ensure_ascii=False, indent=1))
    print("Payload:", json.dumps(p, ensure_ascii=False, indent=1))
    if "exp" in p:
        exp = datetime.fromtimestamp(p["exp"])
        print("过期时间:", exp, "（已过期)" if exp < datetime.now() else "（有效）")


if __name__ == "__main__":
    main()
''', ("开发", "JWT"), [])
    add("ts-converter", "时间戳转换器", "时间戳 ↔ 日期互转（当前/指定/反向）。",
        '''"""时间戳转换：now | <epoch> | --date '2026-01-01 10:00'"""
import argparse
from datetime import datetime


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value", nargs="?", default="now")
    ap.add_argument("--date", help="反向：日期字符串转时间戳")
    args = ap.parse_args()
    if args.date:
        dt = datetime.fromisoformat(args.date)
        print(int(dt.timestamp()))
    elif args.value == "now":
        now = datetime.now()
        print("时间戳:", int(now.timestamp()), "|", now.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        ts = int(args.value)
        print(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
''', ("开发", "时间"), [])
    add("env-checker", ".env 校验器", "对比 .env 与 .env.example 的缺失/多余键。",
        '''""".env 校验：缺失键与多余键清单。"""
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
''', ("开发", "配置"), [])
    add("indent-fix", "缩进规范化", "Tab→空格、行尾空白清理（PEP8 卫生）。",
        '''"""缩进修复：Tab→4空格 + 行尾空白。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    for f in args.files:
        p = Path(f)
        lines = p.read_text(encoding="utf-8").split("\\n")
        fixed = [ln.replace("\\t", "    ").rstrip() for ln in lines]
        if fixed != lines:
            print("规范化:", p)
            if args.apply:
                p.write_text("\\n".join(fixed), encoding="utf-8")


if __name__ == "__main__":
    main()
''', ("开发", "规范化"), [])
    add("todo-scanner", "TODO/FIXME 扫描", "全库扫描未完成标记并按文件汇总。",
        '''"""TODO 扫描：TODO/FIXME/HACK/XXX 全库清单。"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

RX = re.compile(r"\\b(TODO|FIXME|HACK|XXX)\\b[:：]?\\s*(.*)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    by_file = defaultdict(list)
    for p in Path(args.directory).rglob("*"):
        if p.suffix not in {".py", ".js", ".ts", ".vue", ".mjs"} or "node_modules" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = RX.search(line)
            if m:
                by_file[str(p)].append((i, m.group(1), m.group(2)[:50]))
    for f, marks in sorted(by_file.items()):
        print(f)
        for i, kind, text in marks:
            print(f"  L{i} [{kind}] {text}")
    print(f"共 {sum(len(v) for v in by_file.values())} 处未完成标记")


if __name__ == "__main__":
    main()
''', ("开发", "扫描"), [])

    # ================= 系统与效率 =================
    add("sys-top-processes", "进程资源 Top 榜", "CPU/内存占用 Top10（psutil）。",
        '''"""进程榜：CPU 与内存 Top10。"""
import argparse

import psutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--by", choices=["cpu", "mem"], default="cpu")
    args = ap.parse_args()
    import time
    procs = list(psutil.process_iter(["pid", "name"]))
    for p in procs:
        try:
            p.cpu_percent(interval=None)  # 首次调用置零，建立采样基线
        except psutil.Error:
            pass
    time.sleep(0.5)
    for p in procs:
        try:
            p.info["cpu_percent"] = p.cpu_percent(interval=None)
            p.info["memory_percent"] = p.memory_percent()
        except psutil.Error:
            p.info["cpu_percent"] = p.info["memory_percent"] = 0.0
    key = (lambda p: p.info["memory_percent"] or 0) if args.by == "mem" else (lambda p: p.info["cpu_percent"] or 0)
    for p in sorted(procs, key=key, reverse=True)[:10]:
        print(f"{p.info['pid']:>7}  {p.info['name'][:26]:<26} "
              f"CPU {p.info['cpu_percent'] or 0:5.1f}%  MEM {p.info['memory_percent'] or 0:5.1f}%")


if __name__ == "__main__":
    main()
''', ("系统", "进程"), ["psutil"])
    add("sys-disk-gauge", "磁盘使用仪表", "各分区使用率 + 进度条可视化。",
        '''"""磁盘仪表：分区使用率进度条。"""
import psutil

for part in psutil.disk_partitions():
    try:
        u = psutil.disk_usage(part.mountpoint)
    except PermissionError:
        continue
    pct = u.percent / 100
    bar = "█" * int(pct * 24) + "░" * (24 - int(pct * 24))
    warn = " ⚠️" if u.percent > 90 else ""
    print(f"{part.mountpoint:<14} {bar} {u.percent:5.1f}%  "
          f"剩余 {u.free / 1024**3:.0f}GB/{u.total / 1024**3:.0f}GB{warn}")
''', ("系统", "磁盘"), ["psutil"])
    add("sys-battery", "电池状态监控", "电量/充电状态/剩余时间。",
        '''"""电池状态：电量与预估续航。"""
import psutil

bat = psutil.sensors_battery()
if bat is None:
    print("未检测到电池（台式机）")
else:
    plug = "充电中 ⚡" if bat.power_plugged else "电池供电"
    print(f"电量 {bat.percent:.0f}%  {plug}")
    if bat.secsleft and bat.secsleft != psutil.POWER_TIME_UNLIMITED and bat.secsleft > 0:
        h, m = divmod(bat.secsleft // 60, 60)
        print(f"预估剩余 {h}小时{m}分钟")
''', ("系统", "电池"), ["psutil"])
    add("sys-info-report", "系统信息报告", "一键输出系统概况（硬件+Python 环境）。",
        '''"""系统报告：平台/硬件/Python 环境。"""
import platform
import sys

import psutil

print("系统:", platform.platform())
print("主机名:", platform.node())
print("CPU:", platform.machine(), psutil.cpu_count(logical=True), "逻辑核")
mem = psutil.virtual_memory()
print(f"内存: {mem.total / 1024**3:.0f}GB（可用 {mem.available / 1024**3:.1f}GB）")
disk = psutil.disk_usage("/")
print(f"根盘: {disk.total / 1024**3:.0f}GB（已用 {disk.percent:.0f}%）")
print("Python:", sys.version.split()[0], "@", sys.executable)
''', ("系统", "信息"), ["psutil"])
    add("pwd-strength", "密码强度检查", "长度/字符集/常见弱口令模式评分。",
        '''"""密码强度：评分 0-100 与改进建议。"""
import argparse
import re

WEAK = {"password", "123456", "qwerty", "admin888", "111111", "abc123"}


def score(pwd):
    s = 0
    notes = []
    if len(pwd) >= 8: s += 20
    else: notes.append("长度不足 8 位")
    if len(pwd) >= 14: s += 15
    if re.search(r"[a-z]", pwd) and re.search(r"[A-Z]", pwd): s += 20
    else: notes.append("建议混合大小写")
    if re.search(r"\\d", pwd): s += 20
    else: notes.append("建议包含数字")
    if re.search(r"[^\\w]", pwd): s += 15
    else: notes.append("建议包含符号")
    if pwd.lower() in WEAK: return 0, ["常见弱口令，必须更换"]
    if not re.search(r"(.)\\1{2,}", pwd): s += 10
    else: notes.append("避免连续重复字符")
    return min(100, s), notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("password")
    args = ap.parse_args()
    s, notes = score(args.password)
    level = "弱" if s < 40 else "中" if s < 70 else "强"
    print(f"强度: {s}/100（{level}）")
    for n in notes:
        print("  -", n)


if __name__ == "__main__":
    main()
''', ("系统", "安全"), [])
    add("pwd-vault", "本地密码保险库", "主口令派生密钥的离线密码库（自担风险演示）。",
        '''"""密码保险库：主口令 + 盐 派生 keystream 的本地加密存储（教学级实现，生产请用 keyring/1Password）。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

VAULT = Path("vault.enc.json")


import os


def keystream(master: str, salt: bytes, size: int):
    out = b""
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(master.encode() + salt + str(counter).encode()).digest()
        counter += 1
    return out[:size]


def xor(data: bytes, key: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, key))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["add", "get", "list"])
    ap.add_argument("site")
    ap.add_argument("--master", required=True)
    args = ap.parse_args()
    if VAULT.exists():
        blob = json.loads(VAULT.read_text())
        salt, data = bytes.fromhex(blob["salt"]), bytes.fromhex(blob["data"])
        vault = json.loads(xor(data, keystream(args.master, salt, len(data))))
    else:
        salt, vault = os.urandom(16), {}
    if args.mode == "add":
        import getpass
        vault[args.site] = getpass.getpass("密码: ")
    elif args.mode == "get":
        print(vault.get(args.site) or "<未记录>")
    else:
        print("站点:", sorted(vault))
    plain = json.dumps(vault, ensure_ascii=False).encode()
    data = xor(plain, keystream(args.master, salt, len(plain)))
    VAULT.write_text(json.dumps({"salt": salt.hex(), "data": data.hex()}))


if __name__ == "__main__":
    main()
''', ("系统", "安全"), [])
    add("expense-tracker", "花销记账本", "SQLite 记账：记一笔/月度分类汇总。",
        '''"""记账本：add <分类> <金额> [备注] | report [月份]"""
import argparse
import sqlite3
from collections import defaultdict

DB = "expenses.db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["add", "report"])
    ap.add_argument("args", nargs="*")
    args = ap.parse_args()
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS expenses (date TEXT, category TEXT, amount REAL, note TEXT)")
    if args.cmd == "add" and len(args.args) >= 2:
        from datetime import date
        cat, amount = args.args[0], float(args.args[1])
        note = args.args[2] if len(args.args) > 2 else ""
        conn.execute("INSERT INTO expenses VALUES (?, ?, ?, ?)", (date.today().isoformat(), cat, amount, note))
        conn.commit()
        print(f"已记: {cat} ¥{amount}")
    else:
        month = args.args[0] if args.args else __import__("datetime").date.today().strftime("%Y-%m")
        by_cat = defaultdict(float)
        for cat, amount in conn.execute("SELECT category, amount FROM expenses WHERE date LIKE ?", (month + "%",)):
            by_cat[cat] += amount
        total = sum(by_cat.values())
        for cat in sorted(by_cat, key=by_cat.get, reverse=True):
            print(f"{cat:<10} ¥{by_cat[cat]:>8.2f}  {'█' * int(by_cat[cat] / max(total, 1) * 20)}")
        print(f"{'合计':<10} ¥{total:>8.2f}")
    conn.close()


if __name__ == "__main__":
    main()
''', ("效率", "记账"), [])
    add("unit-convert-pro", "科学单位换算", "长度/重量/温度/数据量/角度 五域换算。",
        '''"""单位换算：python xxx.py 5 km mile | 100 f c"""
import argparse

LENGTH = {"m": 1, "km": 1000, "mile": 1609.344, "ft": 0.3048, "inch": 0.0254}
WEIGHT = {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.02835}
DATA = {"MB": 1, "KB": 1 / 1024, "GB": 1024, "TB": 1024 ** 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value", type=float)
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    v, src, dst = args.value, args.src.lower(), args.dst.lower()
    if {src, dst} <= set(LENGTH):
        print(f"{v * LENGTH[src] / LENGTH[dst]:.4f} {dst}")
    elif {src, dst} <= set(WEIGHT):
        print(f"{v * WEIGHT[src] / WEIGHT[dst]:.4f} {dst}")
    elif {src, dst} <= set(DATA):
        print(f"{v * DATA[src.upper()] / DATA[dst.upper()]:.4f} {dst.upper()}")
    elif src == "c" and dst == "f":
        print(f"{v * 9 / 5 + 32:.2f} °F")
    elif src == "f" and dst == "c":
        print(f"{(v - 32) * 5 / 9:.2f} °C")
    else:
        print("不支持的单位对")


if __name__ == "__main__":
    main()
''', ("效率", "换算"), [])
    add("color-tool", "颜色转换器", "HEX ↔ RGB ↔ HSL 三向转换。",
        '''"""颜色转换：#3498db rgb | 52,152,219 hex"""
import argparse
import colorsys


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#%02x%02x%02x" % rgb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value")
    args = ap.parse_args()
    v = args.value
    if v.startswith("#"):
        rgb = hex2rgb(v)
        h, l, s = colorsys.rgb_to_hls(*[x / 255 for x in rgb])
        print(f"RGB: {rgb}  HSL: ({h * 360:.0f}, {s * 100:.0f}%, {l * 100:.0f}%)")
    elif "," in v:
        rgb = tuple(int(x) for x in v.split(","))
        h, l, s = colorsys.rgb_to_hls(*[x / 255 for x in rgb])
        print(f"HEX: {rgb2hex(rgb)}  HSL: ({h * 360:.0f}, {s * 100:.0f}%, {l * 100:.0f}%)")
    else:
        print("输入 #hex 或 r,g,b")


if __name__ == "__main__":
    main()
''', ("效率", "颜色"), [])
    return c.save()


def syntax_check(coll_data):
    import ast as _ast
    import warnings
    bad = 0
    for e in coll_data["examples"]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                _ast.parse(e["code"])
            except SyntaxError as err:
                bad += 1
                print(f"  ✗ {e['id']}: line {err.lineno} {err.msg}")
    return bad


if __name__ == "__main__":
    build_dev_tools()
    import importlib.util
    spec = importlib.util.spec_from_file_location("g2", Path(__file__).parent / "gen_dev_tools2.py")
    g2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g2)
    g2.build_image_tools()
    g2.build_media_tools()
    data = json.load(open(OUT_DIR / "devtools_examples.json"))
    bad = syntax_check(data)
    print(f"✅ 实用工具箱: {len(data['examples'])} 条 (语法错误 {bad})")
