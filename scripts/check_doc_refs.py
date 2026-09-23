#!/usr/bin/env python3
"""文档引用防漂移：校验 README / ROADMAP / docs 中引用的仓库文件真实存在。

单人项目文档最大的退化方式是"文档指向已删除的文件"（本仓库曾连续发生：
ROADMAP 能力矩阵引用 renderer/app.js 等三个已删目录）。本脚本从三处提取引用：
1. Markdown 链接 [text](path)（剥离 #锚点，按文档所在目录解析相对路径）；
2. 反引号路径 `prefix/...`（仅校验已知仓库目录前缀开头、不含通配符的项）；
3. 只读校验，不改任何文件。发现失效引用以退出码 1 报告。

历史存档文档在首部加入 `<!-- doc-refs: skip -->` 即整体跳过校验
（其中的失效引用是历史事实的一部分，不要求修复）。

用法：python3 scripts/check_doc_refs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_MARK = "<!-- doc-refs: skip -->"

# 反引号路径仅校验这些前缀开头的引用（避免把 npm run / RPC 方法名等误当路径）
CHECK_PREFIXES = ("app/", "electron-prototype/", "scripts/", "tests/", "docs/", ".github/", "json_examples/")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")


def doc_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "ROADMAP.md"]
    files.extend(sorted((ROOT / "docs").glob("*.md")))
    return [f for f in files if f.exists()]


def extract_refs(text: str) -> list[str]:
    refs: list[str] = []
    for m in MD_LINK_RE.finditer(text):
        target = m.group(1).strip()
        target = target.split("#", 1)[0]
        if target and not target.startswith(("http://", "https://", "mailto:")):
            refs.append(target)
    for m in BACKTICK_RE.finditer(text):
        cand = m.group(1).strip()
        if cand.startswith(CHECK_PREFIXES) and "*" not in cand and " " not in cand and Path(cand).suffix:
            refs.append(cand)
    return refs


def main() -> int:
    broken: list[tuple[Path, str]] = []
    checked = 0
    for doc in doc_files():
        text = doc.read_text(encoding="utf-8")
        if SKIP_MARK in text[:500]:
            continue  # 存档文档：历史引用不做存在性要求
        for ref in extract_refs(text):
            checked += 1
            # 统一规则：先按文档目录解析（md 相对链接语义），再按仓库根解析
            if not (doc.parent / ref).exists() and not (ROOT / ref).exists():
                broken.append((doc.relative_to(ROOT), ref))
    print(f"[doc-refs] 检查 {len(doc_files())} 个文档中的 {checked} 个文件引用")
    if broken:
        print(f"[doc-refs] 发现 {len(broken)} 个失效引用：")
        for doc, ref in broken:
            print(f"  - {doc}: {ref}")
        return 1
    print("[doc-refs] 全部引用有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
