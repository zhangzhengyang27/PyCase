#!/usr/bin/env python3
"""可运行性基线报告：静态判定全量 + 抽样实跑校准（北极星指标留档）。

两个互补的数字：
- 静态可运行率：app/run_status.py 对全量示例的推定（runnable 占比），秒级、可频繁重跑；
- 实跑通过率：复用 regression_smoke 的分层抽样与子进程试跑管线，是"真跑得通"的
  诚实度量（与 2026-09-09 首轮基线 66.7% 同口径可比）。

并输出静态预测与实跑结果的交叉校准，量化静态检查的盲区（预测 missing_deps
但实跑通过 → 过度拦截；预测 runnable 但实跑失败 → 漏报清单）。

用法（须用共享 .venv 解释器，依赖判定才有意义）：
  .venv/bin/python scripts/run_status_report.py --md docs/run-status-baseline.md
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
for p in (str(ROOT), str(SCRIPT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.json_examples import ExampleStore  # noqa: E402
from app.models import ExampleItem  # noqa: E402
from app.run_status import BROKEN, EMPTY, MISSING_DEPS, RISKY, RUNNABLE, STATUS_LABELS  # noqa: E402

import regression_smoke as rs  # noqa: E402  复用分层抽样与实跑管线

RUN_STATUS_ORDER = [RUNNABLE, MISSING_DEPS, EMPTY, BROKEN, RISKY]


def collect_all(store: ExampleStore) -> list[ExampleItem]:
    """全部 JSON 示例条目（含空壳 __init__.py：它们正是 static 判定要暴露的对象）。"""
    root = store.load()
    items: list[ExampleItem] = []

    def _walk(item: ExampleItem) -> None:
        if not item.is_dir and item.json_id:
            items.append(item)
        for child in item.children:
            _walk(child)

    _walk(root)
    return items


def cross_check(
    static_by_id: dict[str, str], results: list[rs.RunResult]
) -> dict[str, list[str]]:
    """静态预测与实跑结果的交叉校准（仅统计双方都有判定的样本）。"""
    over_block: list[str] = []  # 静态 missing_deps 但实跑 pass：预测过度拦截
    missed: list[str] = []  # 静态 runnable 但实跑失败/缺依赖：静态盲区
    agree_missing = 0  # 静态 missing_deps 且实跑缺依赖：预测命中
    static_missing_total = 0
    for r in results:
        st = static_by_id.get(r.example_id)
        if st is None:
            continue
        if st == MISSING_DEPS:
            static_missing_total += 1
            if r.status == "missing_dependency":
                agree_missing += 1
            elif r.status == "pass":
                over_block.append(f"{r.name}（实跑通过）")
        elif st == RUNNABLE and r.status in {"missing_dependency", "failed", "syntax_error", "timeout", "launch_error"}:
            missed.append(f"{r.name} → 实跑 {r.status}：{r.reason[:60]}")
    return {
        "agree_missing": [f"{agree_missing}/{static_missing_total}"],
        "over_block": over_block,
        "missed": missed,
    }


def build_markdown(
    static_counts: Counter[str],
    total: int,
    results: list[rs.RunResult],
    cross: dict[str, list[str]],
    meta: dict[str, Any],
) -> str:
    static_rate = static_counts.get(RUNNABLE, 0) / max(1, total)
    run_counts = Counter(r.status for r in results)
    pass_n = run_counts.get("pass", 0)
    run_rate = pass_n / max(1, len(results))
    lines = [
        "# 可运行性基线报告",
        "",
        "> 由 `scripts/run_status_report.py` 生成：静态判定全量 + 抽样实跑校准。",
        "> 静态可运行率是「推定」（代码体检），实跑通过率是「真跑得通」的度量，两者互补。",
        "",
        f"- 生成时间：{meta['generated_at']}",
        f"- 示例总数：{total}（解释器 {meta['python']}）",
        f"- 实跑抽样：ratio={meta['ratio']}（seed={meta['seed']}），试跑 {len(results)} 个，超时 {meta['timeout']}s",
        "",
        "## 静态判定（全量）",
        "",
        "| 状态 | 数量 | 占比 |",
        "|---|---|---|",
    ]
    for status in RUN_STATUS_ORDER:
        n = static_counts.get(status, 0)
        lines.append(f"| {STATUS_LABELS[status]}（{status}） | {n} | {n / max(1, total):.1%} |")
    lines += [
        "",
        f"**静态可运行率：{static_rate:.1%}**",
        "",
        "## 抽样实跑（与 regression_smoke 同管线同口径）",
        "",
        "| 状态 | 数量 | 占比 |",
        "|---|---|---|",
    ]
    for status in rs.STATUS_ORDER:
        n = run_counts.get(status, 0)
        if n:
            lines.append(f"| {status} | {n} | {n / max(1, len(results)):.1%} |")
    lines += [
        "",
        f"**实跑通过率：{run_rate:.1%}**（2026-09-09 首轮基线为 66.7%，同 ratio/seed 口径）",
        "",
        "## 静态预测 × 实跑交叉校准",
        "",
        f"- 缺依赖预测命中：{cross['agree_missing'][0]}（静态 missing_deps 且实跑 missing_dependency）",
        "",
    ]
    if cross["over_block"]:
        lines.append("### 预测过度拦截（静态缺依赖但实跑通过，前 10 条）")
        lines += ["", *[f"- {x}" for x in cross["over_block"][:10]], ""]
    if cross["missed"]:
        lines.append("### 静态盲区（推定可运行但实跑失败，前 15 条）")
        lines += ["", *[f"- {x}" for x in cross["missed"][:15]], ""]
    if not cross["over_block"] and not cross["missed"]:
        lines.append("（本批样本内静态预测与实跑无冲突）")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="可运行性基线报告")
    parser.add_argument("--ratio", type=float, default=0.1, help="实跑抽样比例（默认 0.1，与首轮基线一致）")
    parser.add_argument("--seed", type=int, default=42, help="抽样随机种子（默认 42，与首轮基线一致）")
    parser.add_argument("--limit", type=int, default=None, help="最多实跑多少个（调试用）")
    parser.add_argument("--timeout", type=float, default=8.0, help="单示例实跑超时秒数（默认 8）")
    parser.add_argument("--md", type=Path, default=None, help="Markdown 报告输出路径")
    args = parser.parse_args()

    if not all((ROOT / d).exists() for d in ("topics", "tools", "projects")):
        print("[run-status] 未发现示例数据目录，跳过。")
        return 0
    venv_py = ROOT / (".venv/Scripts/python.exe" if sys.platform == "win32" else ".venv/bin/python")
    python_exe = str(venv_py) if venv_py.exists() else sys.executable

    store = ExampleStore(base_dir=ROOT)
    items = collect_all(store)
    if not items:
        print("[run-status] 未加载到任何示例，跳过。")
        return 0
    store.set_module_python(python_exe)

    # 1) 全量静态判定
    started = time.time()
    static_counts: Counter[str] = Counter()
    static_by_id: dict[str, str] = {}
    for it in items:
        st = store.ensure_run_status(it)
        static_counts[st] += 1
        static_by_id[it.json_id or it.name] = st
    print(f"[run-status] 静态判定 {len(items)} 条（{time.time() - started:.1f}s）：" + "，".join(f"{s}={static_counts.get(s, 0)}" for s in RUN_STATUS_ORDER))

    # 2) 抽样实跑校准（叶子、排除 __init__.py，与 regression_smoke 口径一致）
    leaves = [it for it in items if it.name != "__init__.py"]
    sample = rs.stratified_sample(leaves, args.ratio, args.seed, args.limit)
    print(f"[run-status] 实跑抽样 {len(sample)} 条，解释器 {python_exe}")
    results = []
    for idx, item in enumerate(sample, 1):
        result = rs.run_one(item, python_exe, args.timeout)
        results.append(result)
        if idx % 20 == 0:
            print(f"  [{idx}/{len(sample)}] …")
    run_counts = Counter(r.status for r in results)
    print("[run-status] 实跑汇总：" + "，".join(f"{s}={run_counts.get(s, 0)}" for s in rs.STATUS_ORDER))

    # 3) 交叉校准 + 报告
    cross = cross_check(static_by_id, results)
    meta = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "ratio": args.ratio,
        "seed": args.seed,
        "timeout": args.timeout,
        "python": sys.version.split()[0],
    }
    markdown = build_markdown(static_counts, len(items), results, cross, meta)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(markdown, encoding="utf-8")
        print(f"[run-status] 报告已写入 {args.md}")
    else:
        print("\n" + markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
