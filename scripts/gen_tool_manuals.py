#!/usr/bin/env python3
"""生成工具手册数据（tool-manuals.json）——W7 手册页基座。

从内置库每个「工具」条目的源码中提取：
- 概述 = 模块 docstring 首段
- 参数表 = argparse 的 add_argument 调用（flag/类型/默认值/help）
- 用法 = docstring 里 `python xxx.py ...` 形态的首行（无则由标题合成）

排除两类：
- 已有交互页的工具（标题排除表，正则测试器等 15 个 CLI 与交互页并存，手册冗余）
- 页面化反而更差的 4 个（密码保险库/番茄钟/文件变更监听/站点可用性监控，见规划 §8.2）

产物：electron-prototype/electron/src/renderer/src/tool-manuals.json
用法：python scripts/gen_tool_manuals.py（幂等；tests/test_tool_manuals.py 钉覆盖率与新鲜度）
"""

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "electron-prototype/electron/src/renderer/src/tool-manuals.json"

# 已有交互页的 CLI 工具（标题精确匹配）：交互页即其文档，手册冗余
EXCLUDE_INTERACTIVE = {
    "正则测试器", "JSON 格式化校验", "JSON → dataclass", "CSV ↔ JSON 互转",
    "时间戳转换器", "UUID/短 ID 生成器", "颜色转换器", "科学单位换算", "密码强度检查",
    "CSV ↔ Excel 互转", "PDF 文本提取", "图片转 PDF", "图片批量水印", "密码生成器",
    "图片批量压缩",
}
# 页面化反而更差（规划 §8.2 保持原样）
EXCLUDE_UNFIT = {
    "本地密码保险库", "命令行番茄钟", "文件变更监听", "站点可用性监控",
}
EXCLUDE = EXCLUDE_INTERACTIVE | EXCLUDE_UNFIT

# 演示教学簇（标题含这些词 → 附教学注记）
DEMO_NOTE = "教学示例：脚本内数据为演示硬编码；实际使用把数据源换成真实文件/目录即可。"
DEMO_TITLE_PATTERNS = ("Excel", "Word", "PPT", "邮件", "日报", "待办", "盘点", "字符方阵", "文本表格")


def extract_params(code: str) -> list[dict]:
    """从 argparse 的 add_argument 调用提取参数表（ast 解析，容错）。"""
    params: list[dict] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return params
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "add_argument"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        entry: dict = {"flag": first.value}
        for kw in node.keywords:
            name = kw.arg
            if name == "type" and isinstance(kw.value, ast.Name):
                entry["type"] = kw.value.id
            elif name == "default" and isinstance(kw.value, ast.Constant):
                entry["default"] = kw.value.value
            elif name == "action" and isinstance(kw.value, ast.Constant):
                entry["action"] = kw.value.value
            elif name == "help" and isinstance(kw.value, ast.Constant):
                entry["help"] = kw.value.value
            elif name == "nargs" and isinstance(kw.value, ast.Constant):
                entry["nargs"] = kw.value.value
        if not entry["flag"].startswith("-"):
            entry["positional"] = True
        params.append(entry)
    return params


def build_entry(e: dict, code: str) -> dict:
    doc = ast.get_docstring(ast.parse(code)) or ""
    first_para = doc.split("\n\n")[0].strip() if doc else (e.get("description") or "").strip()
    # 用法行：docstring 中 `python xxx.py ...` 形态优先，否则由标题合成
    usage = ""
    m = re.search(r"python\s+\S+\.py[^\n]*", doc)
    if m:
        usage = m.group(0).strip()
    if not usage:
        usage = f"python {e.get('name', 'tool.py')}"
    entry = {
        "title": e.get("title") or e.get("name", "").replace(".py", ""),
        "summary": first_para,
        "usage": usage,
        "params": extract_params(code),
    }
    if any(pat in entry["title"] for pat in DEMO_TITLE_PATTERNS):
        entry["notes"] = [DEMO_NOTE]
    return entry


def main() -> int:
    root = ROOT / "json_examples"
    manuals: dict[str, dict] = {}
    total = 0
    skipped = 0
    for p in sorted(root.glob("*.json")):
        if p.name == "facts.json":
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for e in data.get("examples", []):
            if e.get("category") != "tools":
                continue
            total += 1
            title = e.get("title") or ""
            if title in EXCLUDE:
                skipped += 1
                continue
            code_path = root / e.get("file", "")
            if not code_path.is_file():
                print(f"[warn] 缺源码，跳过 {e['id']}", file=sys.stderr)
                skipped += 1
                continue
            manuals[e["id"]] = build_entry(e, code_path.read_text(encoding="utf-8"))
    out = {
        "comment": "工具手册数据（W7 手册页基座）：由 scripts/gen_tool_manuals.py 从工具源码生成（docstring 概述 + argparse 参数表 + 用法行）。勿手改——改生成器后重跑；tests/test_tool_manuals.py 钉覆盖率与新鲜度。",
        "manuals": dict(sorted(manuals.items())),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✅ 手册 {len(manuals)} 份（工具总数 {total}，排除 {skipped}）→ {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
