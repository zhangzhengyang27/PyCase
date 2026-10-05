#!/usr/bin/env python3
"""语料真实执行验证器：把「全库示例逐个真跑 + 分类」从会话内临时取证固化为常备工具。

背景（2026-10 三轮审计的方法论收口）：静态检查（parse + imports 可解析）对
「碎片文件」「必崩代码」全数误报 runnable，运行意义只能靠真实执行判定。本工具
逐条运行 facts.json 里的语料文件（独立临时 cwd + 超时 + 并行），按既定口径分类，
「意外类」非空即退出码 1——占位引导/网络/GUI 等既定语义经豁免清单显式声明。

分类口径（与 2026-10-04 语料真实性排查一致）：
  OK           exit 0 且（有 stdout 或产生了非空产物文件）
  EMPTY        exit 0 但无任何可观察行为（可疑，需人工判读）
  NEEDS_ARGS   argparse 用法报错（exit 2）——演示型工具的既定语义
  NEEDS_DATA   运行期 FileNotFoundError——需要输入文件的既定语义
  IMPORT_ERROR ModuleNotFoundError——缺依赖，需修 requirements 或代码
  GUI_BLOCK    超时且 stderr 呈 Tk/pygame/turtle 事件循环特征——弹窗型既定语义
  TIMEOUT      超时但无 GUI 特征——真挂起，需人工判读
  ERROR        其余非零退出——真 bug，必须修
  ALLOWED      命中豁免清单（scripts/verify_corpus_allowlist.txt：id + 可接受类别）

matplotlib 示例统一注入 MPLBACKEND=Agg（无头出图；tkinter 弹窗型仍会超时归 GUI_BLOCK）。
工具交互页的 pyCode（TS schema 内联）不在本工具口径内——其转储与执行由 vitest
schemas-pyexec.spec.ts 及后续 dump 管线承接。

用法：
  .venv/bin/python scripts/verify_corpus.py                 # 全量 445 条
  .venv/bin/python scripts/verify_corpus.py --limit 30      # 抽样
  .venv/bin/python scripts/verify_corpus.py --json out.json # 机器可读报告
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "json_examples" / "facts.json"
ALLOWLIST = ROOT / "scripts" / "verify_corpus_allowlist.txt"
FACTS_URL = "json_examples/facts.json"

GUI_MARKERS = ("tkinter", "pygame", "turtle", "mainloop", "TclError")
GUI_SOURCE_MARKERS = ("import turtle", "import pygame", "tkinter", "imshow(")
ARGPARSE_MARKERS = ("the following arguments are required", "usage:")


def classify(exit_code: int, stdout: str, stderr: str, timed_out: bool, artifacts: int, source: str = "") -> str:
    """纯分类函数：依据运行结果给出判定（无 IO，便于测试）。

    source 是示例源码文本：超时且 stderr 干净是 turtle/pygame/imshow 弹窗型的常态
    （事件循环静默驻留，stderr 无特征），必须回源码看 import 才能归 GUI_BLOCK。
    """
    if timed_out:
        if any(m in stderr for m in GUI_MARKERS) or any(m in source for m in GUI_SOURCE_MARKERS):
            return "GUI_BLOCK"
        return "TIMEOUT"
    if exit_code == 0:
        return "OK" if (stdout.strip() or artifacts) else "EMPTY"
    if exit_code == 2 and any(m in stderr for m in ARGPARSE_MARKERS):
        return "NEEDS_ARGS"
    if "ModuleNotFoundError" in stderr:
        return "IMPORT_ERROR"
    if "FileNotFoundError" in stderr:
        return "NEEDS_DATA"
    return "ERROR"


def load_allowlist(path: Path) -> dict[str, set[str]]:
    """豁免清单：每行 `id verdict [reason…]`；同一 id 可声明多个可接受类别。

    `prefix:<前缀> verdict [reason…]` 形态按 id 前缀匹配——网络依赖类（爬虫实战等）
    的具体哪条失败随环境漂移（限流/代理/断网），逐条枚举不胜其烦，按家族声明。
    """
    table: dict[str, set[str]] = {}
    if not path.exists():
        return table
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        table.setdefault(parts[0], set()).add(parts[1])
    return table


def allow_verdicts_for(table: dict[str, set[str]], item_id: str) -> set[str]:
    """合并精确 id 与 prefix: 前缀两类豁免条目。"""
    accepted = set(table.get(item_id, ()))
    for key, verdicts in table.items():
        if key.startswith("prefix:") and item_id.startswith(key[len("prefix:"):]):
            accepted |= verdicts
    return accepted


def run_one(python: str, rel_file: str, timeout: float) -> dict:
    source = (ROOT / rel_file).read_text(encoding="utf-8", errors="replace")
    with tempfile.TemporaryDirectory(prefix="pycase-verify-") as td:
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
        try:
            proc = subprocess.run(
                [python, str(ROOT / rel_file)],
                cwd=td,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            exit_code, stdout, stderr, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as e:
            exit_code, timed_out = 124, True
            stdout = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        artifacts = sum(1 for p in Path(td).rglob("*") if p.is_file() and p.stat().st_size > 0)
    return {
        "exit": exit_code,
        "stdout_lines": len(stdout.splitlines()),
        "artifacts": artifacts,
        "timed_out": timed_out,
        "verdict": classify(exit_code, stdout, stderr, timed_out, artifacts, source),
        "stderr_tail": stderr.strip().splitlines()[-3:],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="语料真实执行验证器（意外类非空 → 退出码 1）")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条（抽样用）")
    ap.add_argument("--ids", default="", help="只跑这些 id（逗号分隔）")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--json", dest="json_out", default="", help="把完整结果写入该 JSON 文件")
    args = ap.parse_args()

    items = json.loads(FACTS.read_text(encoding="utf-8"))["items"]
    if args.ids:
        wanted = [s.strip() for s in args.ids.split(",") if s.strip()]
        unknown = [w for w in wanted if w not in items]
        if unknown:
            sys.exit(f"未知 id: {unknown}")
        targets = {k: items[k] for k in wanted}
    else:
        targets = dict(list(items.items())[: args.limit] if args.limit else items.items())

    python = str(ROOT / ".venv" / "bin" / "python")
    if not Path(python).exists():
        python = sys.executable

    allow = load_allowlist(ALLOWLIST)
    print(f"验证 {len(targets)} 条（解释器 {python}，超时 {args.timeout}s，并行 {args.workers}）…")

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {k: pool.submit(run_one, python, v["file"], args.timeout) for k, v in targets.items()}
        for i, (key, fut) in enumerate(futures.items(), 1):
            results[key] = fut.result()
            if i % 50 == 0 or i == len(futures):
                print(f"  已完成 {i}/{len(futures)}")

    for key, r in results.items():
        accepted = allow_verdicts_for(allow, key)
        if r["verdict"] in accepted and r["verdict"] != "OK":
            r["verdict"] = "ALLOWED"
            r["allow_reason"] = f"豁免清单声明可接受: {sorted(accepted)}"

    by_class: dict[str, list[str]] = {}
    for key, r in results.items():
        by_class.setdefault(r["verdict"], []).append(key)

    print("\n== 分类汇总 ==")
    for cls in ["OK", "ALLOWED", "NEEDS_ARGS", "NEEDS_DATA", "GUI_BLOCK", "EMPTY", "TIMEOUT", "IMPORT_ERROR", "ERROR"]:
        if cls in by_class:
            print(f"  {cls}: {len(by_class[cls])}")

    unexpected = {c: by_class[c] for c in ("ERROR", "IMPORT_ERROR", "TIMEOUT", "EMPTY") if c in by_class}
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"summary": {k: len(v) for k, v in by_class.items()}, "results": results},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n完整结果已写入 {args.json_out}")

    if unexpected:
        print(f"\n⛔ 意外类 {sum(len(v) for v in unexpected.values())} 条（需人工判读/修复）:")
        for cls, keys in unexpected.items():
            for key in keys[:10]:
                tail = "; ".join(results[key]["stderr_tail"][-2:])
                print(f"  [{cls}] {key}" + (f" — {tail}" if tail else ""))
            if len(keys) > 10:
                print(f"    … 以及另外 {len(keys) - 10} 条")
        sys.exit(1)
    print("\n✅ 无意外类（占位引导/需数据/GUI 等既定语义见 --json 或豁免清单）")


if __name__ == "__main__":
    main()
