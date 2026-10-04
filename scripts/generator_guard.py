#!/usr/bin/env python3
"""清单再生成守卫：生成器重跑前对账 id 集，防止已退役条目复活或存活条目静默丢失。

背景（2026-10 体检 P2）：语料大退役（1464→395）后，历史生成器仍内嵌全部历史条目
定义——重跑会把已退役条目写回清单（复活），整文件重写型生成器还可能把后批加入
的条目覆盖掉（丢失）。守卫把「当前清单」当真相：生成 id 集与目标清单 id 集双向
不对账即中止；确要新增/收缩时用 force=True 显式豁免。新增条目的正规流程是改
生成器源码并人工复核差异，而不是靠重跑兜底。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def guard_regen(target: Path, generated: list[dict], *, tool: str, force: bool = False) -> None:
    """对账 generated 与 target 清单的 id 集；有差且未 force 则打印差异并以退出码 2 中止。"""
    current_ids: set[str] = set()
    if target.exists():
        loaded = json.loads(target.read_text(encoding="utf-8"))
        current_ids = {e.get("id", "") for e in loaded.get("examples", [])}
        current_ids.discard("")
    gen_ids = {e.get("id", "") for e in generated}
    gen_ids.discard("")
    resurrected = sorted(gen_ids - current_ids)
    dropped = sorted(current_ids - gen_ids)
    if not resurrected and not dropped:
        return
    if force:
        print(f"⚠️ {tool}: --force 豁免对账差异（复活 {len(resurrected)} / 丢失 {len(dropped)}）")
        return
    print(f"⛔ {tool}: 拒绝写出 {target}", file=sys.stderr)
    if resurrected:
        print(f"  将复活 {len(resurrected)} 个不在当前清单的条目（多为已退役）:", file=sys.stderr)
        for i in resurrected[:20]:
            print(f"    + {i}", file=sys.stderr)
        if len(resurrected) > 20:
            print(f"    … 以及另外 {len(resurrected) - 20} 个", file=sys.stderr)
    if dropped:
        print(f"  将丢失 {len(dropped)} 个当前清单已有条目:", file=sys.stderr)
        for i in dropped[:20]:
            print(f"    - {i}", file=sys.stderr)
        if len(dropped) > 20:
            print(f"    … 以及另外 {len(dropped) - 20} 个", file=sys.stderr)
    print("  确认无误后用 --force（或 Collection.allow_unsafe_write=True）豁免。", file=sys.stderr)
    raise SystemExit(2)
