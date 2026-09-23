#!/usr/bin/env python3
"""示例库第二轮审计处置（2026-09-11，981 集合专项）：确定性、幂等；删除项靠 git 历史回滚。

A. 下架 12 条（仅移出 JSON，源文件按「原文件保留」约定留在磁盘）：
   - 11 条空壳：去 docstring 后无实际语句，运行无意义（test01/test02/example01/
     example02/pip-image/pip3-image/pdf1/word1/2-name/task-02/settings.py）；
     其中 settings.py 是 flask-mumunote 项目配置文件混入，源文件本就在项目目录。
   - 1 条缺依赖：05-docx-to-pdf.py（pydocx 已废弃）。其余缺依赖示例保留作只读
     参考（autotest/C01/C1104/corner_widget 为私有/项目本地模块无法安装，卡片
     已有「缺依赖」徽标）。
B. 摘高危标 3 条：clock.py / marquee.py / tic-tac-toe.py 因 os.system('clear')
   清屏被安全扫描判 HIGH；改为 TTY 探测 + ANSI 转义（真实终端照常清屏，管道/
   应用输出面板下不输出乱码）。function4.py 本身是 os.system 教学示例，保留。

用法（默认 dry-run 打印计划，--apply 才写盘；须用共享 .venv 解释器）：
  .venv/bin/python scripts/fix_examples_round2.py [--apply]
"""

from __future__ import annotations

import ast
import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATED = ROOT / "json_examples" / "migrated.json"

# 下架清单：(name, 审计时的 migrated.json 行号索引)。按 id 摘除，name 双重校验。
REMOVE = [
    ("test01.py", 328),
    ("test02.py", 329),
    ("example01.py", 331),
    ("example02.py", 332),
    ("pip-image.py", 412),
    ("pip3-image.py", 621),
    ("05-docx-to-pdf.py", 289),
    ("pdf1.py", 490),
    ("word1.py", 493),
    ("2-name.py", 674),
    ("task-02.py", 916),
    ("settings.py", 974),
]

CLEAR_BLOCK = "{indent}if sys.stdout.isatty():\n{indent}    print('\\033[2J\\033[H', end='')  # ANSI 清屏（真实终端生效，管道下不输出乱码）"


def fix_clear_screen(code: str, name: str) -> str:
    """os.system('clear') → TTY 探测 + ANSI；import os → import sys。行级精确替换。"""
    out: list[str] = []
    replaced = 0
    for line in code.split("\n"):
        stripped = line.strip()
        indent = line[: len(line) - len(line.lstrip())]
        if stripped.startswith("#") and "os.system('cls')" in stripped:
            continue  # 丢弃指向旧做法的注释
        if stripped == "os.system('clear')":
            out.append(CLEAR_BLOCK.format(indent=indent))
            replaced += 1
            continue
        if stripped == "import os":
            out.append(line.replace("import os", "import sys"))
            continue
        out.append(line)
    new_code = "\n".join(out)
    if replaced == 0:
        raise SystemExit(f"{name}: 未找到 os.system('clear')，中止")
    if "os.system" in new_code or "import os" in new_code:
        raise SystemExit(f"{name}: 残留 os 用点，中止")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ast.parse(new_code)  # 语法必须仍然有效
    return new_code


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(MIGRATED.read_text(encoding="utf-8"))
    examples = data["examples"]
    before = len(examples)

    # A. 按 id 摘除（name 双重校验防错删）
    doomed: set[str] = set()
    for name, idx in REMOVE:
        entry = examples[idx]
        if entry.get("name") != name:
            raise SystemExit(f"#{idx} 期望 {name}，实际 {entry.get('name')}，中止")
        doomed.add(entry["id"])
    kept = [it for it in examples if it["id"] not in doomed]
    removed = before - len(kept)

    # B. 清屏三例
    edited: list[str] = []
    for name, idx in [("clock.py", 483), ("marquee.py", 539), ("tic-tac-toe.py", 543)]:
        entry = examples[idx]
        if entry.get("name") != name:
            raise SystemExit(f"#{idx} 期望 {name}，实际 {entry.get('name')}，中止")
        entry["code"] = fix_clear_screen(entry["code"], name)
        edited.append(name)

    print(f"计划：下架 {removed} 条（{before} → {len(kept)}）；摘高危 {len(edited)} 条：{', '.join(edited)}")
    if not apply:
        print("dry-run 未写盘；确认后加 --apply")
        return

    data["examples"] = kept
    MIGRATED.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写盘：{MIGRATED}")


if __name__ == "__main__":
    main()
