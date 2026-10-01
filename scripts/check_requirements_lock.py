#!/usr/bin/env python3
"""依赖锁一致性门禁：requirements.lock.txt 必须覆盖 requirements.txt 的全部直接依赖。

为什么是「名字级覆盖」而不是字节级 diff：锁的职责是**可复现**（把解析结果钉住），
不是追新——上游发新版不应把 CI 打红；真正要挡的回归是「改了 requirements.txt
却忘了重新生成锁」。

用法：
    python scripts/check_requirements_lock.py          # 校验，不一致退出 1
    uv pip compile requirements.txt -o requirements.lock.txt --universal --header --strip-extras
                                                       # 不一致时重新生成

只校验直接依赖（传递依赖的解析交给 uv，名字可能随解析器策略合法地增减）；
名字按 PEP 503 归一化（小写、`[-_.]+` 折叠为 `-`）后比较。
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock.txt"


def norm(name: str) -> str:
    """PEP 503 规范化：小写、连续 [-_.] 折叠为单个 -。"""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def direct_deps(text: str) -> set[str]:
    """清单直接依赖名字集：去注释、去环境标记、去版本/extras 说明。"""
    out: set[str] = set()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()
        if not line:
            continue
        out.add(norm(re.split(r"[\[=<>!~ ]", line, maxsplit=1)[0]))
    return {n for n in out if n}


def locked_names(text: str) -> set[str]:
    """锁文件里 `name==版本` 行的名字集（uv 输出格式，`# via` 注释行自动跳过）。"""
    out: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==", line)
        if m:
            out.add(norm(m.group(1)))
    return out


def main() -> int:
    if not MANIFEST.exists():
        print(f"[lock] 缺少 {MANIFEST.name}")
        return 1
    if not LOCK.exists():
        print(f"[lock] 缺少 {LOCK.name}——重新生成：")
        print("  uv pip compile requirements.txt -o requirements.lock.txt --universal --header --strip-extras")
        return 1

    deps = direct_deps(MANIFEST.read_text(encoding="utf-8"))
    locked = locked_names(LOCK.read_text(encoding="utf-8"))
    missing = deps - locked
    if missing:
        print(f"[lock] 锁未覆盖 {len(missing)} 个直接依赖: {sorted(missing)}")
        print("重新生成：uv pip compile requirements.txt -o requirements.lock.txt --universal --header --strip-extras")
        return 1
    print(f"[lock] 一致：锁覆盖全部 {len(deps)} 个直接依赖")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
