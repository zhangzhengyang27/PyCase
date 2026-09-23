#!/usr/bin/env python3
"""示例抽样回归脚本（本地质量门，不依赖 Electron）。

对仓库中的 Python 示例做分层抽样并以子进程真实运行，按结果分类：
  pass / failed / missing_dependency / syntax_error / timeout / needs_args / launch_error

设计要点：
- 分层：按 category（topics/tools/projects）比例抽样，保证每个非空分层至少 1 个；
  额外保证 pygame/cv2/PIL/matplotlib/turtle 五个 import 家族至少各覆盖 1 个。
- 安全：复用 sidecar.server 的环境变量白名单与 argparse 静态解析；
  必填位置/选项参数的示例标记 needs_args 直接跳过，不算失败。
- 干净：运行前快照示例目录，运行后删除新生成的文件，仓库不被运行产物污染。
- 基线：--write-baseline 写入基线；--baseline 对比，pass 退化为 failed/syntax_error
  视为回归并以退出码 1 报告。CI 中若示例数据目录不存在则跳过（退出码 0）。

用法：
  python scripts/regression_smoke.py --ratio 0.1          # 抽样 10% 试跑
  python scripts/regression_smoke.py --all                # 全量（耗时较长）
  python scripts/regression_smoke.py --write-baseline tests/fixtures/regression_baseline.json
  python scripts/regression_smoke.py --baseline tests/fixtures/regression_baseline.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
SIDECAR_DIR = ROOT / "electron-prototype" / "sidecar"
for p in (str(ROOT), str(SIDECAR_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.json_examples import ExampleStore  # noqa: E402
from app.models import ExampleItem  # noqa: E402

import server  # noqa: E402

# 视为"回归"的退化方向：基线通过、当前变成这些状态
REGRESSED_TO = {"failed", "syntax_error", "launch_error"}
# 无头运行环境：避免图形后端阻塞导致的假超时
HEADLESS_ENV = {"MPLBACKEND": "Agg", "SDL_VIDEODRIVER": "dummy", "PYGAME_HIDE_SUPPORT_PROMPT": "1"}
STATUS_ORDER = ["pass", "needs_args", "missing_dependency", "timeout", "syntax_error", "failed", "launch_error"]
FAMILIES = {
    "pygame": r"^\s*(?:import|from)\s+pygame\b",
    "cv2": r"^\s*(?:import|from)\s+cv2\b",
    "PIL": r"^\s*(?:import|from)\s+(?:PIL|Pillow)\b",
    "matplotlib": r"\bmatplotlib\b",
    "turtle": r"^\s*(?:import|from)\s+turtle\b",
}


@dataclass
class RunResult:
    """单个示例的试跑结果。"""

    example_id: str
    name: str
    category: str
    status: str
    duration_sec: float
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.example_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "duration_sec": round(self.duration_sec, 2),
            "reason": self.reason,
        }


@dataclass
class _SamplePlan:
    """抽样计划：分层抽样 + 家族覆盖补足。"""

    picked: list[ExampleItem] = field(default_factory=list)

    def ids(self) -> set[str]:
        return {item.json_id for item in self.picked if item.json_id}


def collect_leaves() -> list[ExampleItem]:
    """收集全部叶子示例（排除 __init__.py 与无 json_id 的节点）。"""
    store = ExampleStore(base_dir=ROOT)
    root = store.load()
    leaves: list[ExampleItem] = []

    def _walk(item: ExampleItem) -> None:
        if not item.is_dir and item.json_id and item.name != "__init__.py":
            leaves.append(item)
        for child in item.children:
            _walk(child)

    _walk(root)
    return leaves


def needs_arguments(code: str) -> bool:
    """示例是否声明了必填参数（无默认值的必填项无法在回归中自动运行）。"""
    for spec in server._parse_argparse_from_code(code):  # noqa: SLF001 - 复用 sidecar 纯函数
        if spec.get("required"):
            return True
        if spec.get("is_positional") and spec.get("default") is None:
            return True
    return False


def stratified_sample(
    leaves: list[ExampleItem],
    ratio: float,
    seed: int,
    limit: int | None = None,
) -> list[ExampleItem]:
    """按 category 分层做确定性抽样，并补足五个 import 家族的覆盖。

    >>> items = []  # 仅说明：真实输入为 ExampleItem 列表
    """
    rng = random.Random(seed)
    groups: dict[str, list[ExampleItem]] = defaultdict(list)
    for item in leaves:
        groups[item.category or "unknown"].append(item)

    plan = _SamplePlan()
    for category in sorted(groups):
        members = groups[category][:]
        rng.shuffle(members)
        if ratio >= 1.0:
            chosen = members
        else:
            k = max(1, round(len(members) * ratio))
            chosen = members[:k]
        plan.picked.extend(chosen)

    # 家族覆盖：每个家族至少 1 个（若该家族存在且尚未被抽中）
    import re

    for family, pattern in FAMILIES.items():
        if any(_family_of(item) == family for item in plan.picked):
            continue
        candidates = [
            item
            for item in leaves
            if item.json_id not in plan.ids() and re.search(pattern, item.code or "", re.MULTILINE)
        ]
        if candidates:
            rng.shuffle(candidates)
            plan.picked.append(candidates[0])

    rng.shuffle(plan.picked)
    if limit is not None and len(plan.picked) > limit:
        plan.picked = plan.picked[:limit]
    return plan.picked


def _family_of(item: ExampleItem) -> str | None:
    import re

    for family, pattern in FAMILIES.items():
        if re.search(pattern, item.code or "", re.MULTILINE):
            return family
    return None


def classify_output(exit_code: int, output: str) -> tuple[str, str]:
    """根据退出码与合并输出分类失败原因，返回 (status, reason 摘要)。"""
    if exit_code == 0:
        return "pass", ""
    tail = output.strip().splitlines()[-1][:300] if output.strip() else ""
    if "ModuleNotFoundError" in output or "ImportError" in output:
        return "missing_dependency", tail
    if "SyntaxError" in output:
        return "syntax_error", tail
    return "failed", tail


def _cleanup_new_artifacts(work_dir: Path, snapshot: set[str]) -> None:
    """删除运行后新出现的文件/目录（运行产物不进仓库）。"""
    for name in set(os.listdir(work_dir)) - snapshot:
        target = work_dir / name
        try:
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            else:
                target.unlink(missing_ok=True)
        except OSError:
            pass


def resolve_python(override: str | None) -> str:
    """解析运行示例用的解释器：优先共享 .venv，其次当前解释器。"""
    if override:
        return override
    venv_py = ROOT / (".venv/Scripts/python.exe" if sys.platform == "win32" else ".venv/bin/python")
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def run_one(item: ExampleItem, python_exe: str, timeout: float) -> RunResult:
    """真实运行单个示例并返回结果。"""
    started = time.time()
    code = item.code or ""
    if needs_arguments(code):
        return RunResult(item.json_id or item.name, item.name, item.category, "needs_args", 0.0, "声明了必填参数")

    script_path = item.path
    if not script_path.exists():
        return RunResult(
            item.json_id or item.name, item.name, item.category, "launch_error", 0.0, "脚本文件不存在（数据目录缺失？）"
        )

    work_dir = script_path.parent
    snapshot = set(os.listdir(work_dir))
    pythonpath = os.pathsep.join([*item.run_pythonpath, str(ROOT), os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    env = server._build_safe_env({**HEADLESS_ENV, "PYTHONPATH": pythonpath, "PYTHONUNBUFFERED": "1"})  # noqa: SLF001

    try:
        proc = subprocess.run(
            [python_exe, str(script_path)],
            cwd=str(work_dir),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            text=True,
            errors="replace",
        )
        status, reason = classify_output(proc.returncode, proc.stdout or "")
    except subprocess.TimeoutExpired as exc:
        status, reason = "timeout", f"超过 {timeout}s 未退出"
        _ = exc
    except OSError as exc:
        status, reason = "launch_error", str(exc)[:300]
    finally:
        _cleanup_new_artifacts(work_dir, snapshot)

    return RunResult(
        item.json_id or item.name, item.name, item.category, status, round(time.time() - started, 2), reason
    )


def build_markdown(results: list[RunResult], meta: dict[str, Any]) -> str:
    """生成 Markdown 摘要。"""
    counts = Counter(r.status for r in results)
    lines = [
        "# 示例抽样回归报告",
        "",
        f"- 生成时间：{meta['generated_at']}",
        f"- 抽样比例：{meta['ratio']}（seed={meta['seed']}），试跑 {len(results)} 个",
        f"- 解释器：{meta['python']}",
        "",
        "| 状态 | 数量 | 占比 |",
        "|---|---|---|",
    ]
    total = max(1, len(results))
    for status in STATUS_ORDER:
        n = counts.get(status, 0)
        if n:
            lines.append(f"| {status} | {n} | {n / total:.1%} |")
    problem = [r for r in results if r.status in REGRESSED_TO or r.status in {"missing_dependency", "timeout"}]
    if problem:
        lines += [
            "",
            "## 非通过样本（前 30 条）",
            "",
            "| 示例 | 分类 | 状态 | 耗时(s) | 原因 |",
            "|---|---|---|---|---|",
        ]
        for r in problem[:30]:
            reason = r.reason.replace("|", "/").replace("\n", " ")[:80]
            lines.append(f"| {r.name} | {r.category} | {r.status} | {r.duration_sec} | {reason} |")
    lines.append("")
    return "\n".join(lines)


def compare_baseline(results: list[RunResult], baseline_path: Path) -> list[RunResult]:
    """与基线对比，返回发生回归的样本。"""
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    old_status = {entry["id"]: entry["status"] for entry in baseline.get("results", [])}
    regressions: list[RunResult] = []
    for r in results:
        if old_status.get(r.example_id) == "pass" and r.status in REGRESSED_TO:
            regressions.append(r)
    return regressions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="示例抽样回归脚本")
    parser.add_argument("--ratio", type=float, default=0.1, help="每个分类的抽样比例（0-1，默认 0.1）")
    parser.add_argument("--all", action="store_true", help="全量运行（覆盖 --ratio）")
    parser.add_argument("--seed", type=int, default=42, help="抽样随机种子，保证可复现")
    parser.add_argument("--limit", type=int, default=None, help="最多运行多少个（调试用）")
    parser.add_argument("--timeout", type=float, default=8.0, help="单示例超时秒数（默认 8）")
    parser.add_argument("--python", default=None, help="运行示例的解释器路径（默认共享 .venv）")
    parser.add_argument("--baseline", type=Path, default=None, help="对比的基线 JSON，出现回归则退出码 1")
    parser.add_argument("--write-baseline", type=Path, default=None, help="把本次结果写成基线 JSON")
    parser.add_argument("--md", type=Path, default=None, help="同时把 Markdown 报告写入该路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # CI / 新克隆环境：示例原始数据目录被 gitignore，没有数据时直接跳过
    if not all((ROOT / d).exists() for d in ("topics", "tools", "projects")):
        print("[regression] 未发现 topics/tools/projects 示例数据目录，跳过抽样回归。")
        return 0

    leaves = collect_leaves()
    if not leaves:
        print("[regression] ExampleStore 未加载到任何示例，跳过。")
        return 0

    ratio = 1.0 if args.all else args.ratio
    sample = stratified_sample(leaves, ratio, args.seed, args.limit)
    python_exe = resolve_python(args.python)
    print(f"[regression] 共 {len(leaves)} 个示例，本次抽样 {len(sample)} 个，解释器 {python_exe}")

    results: list[RunResult] = []
    for idx, item in enumerate(sample, 1):
        result = run_one(item, python_exe, args.timeout)
        results.append(result)
        if idx % 10 == 0 or result.status not in {"pass", "needs_args"}:
            print(f"  [{idx}/{len(sample)}] {result.status:18s} {item.name}")

    counts = Counter(r.status for r in results)
    print("[regression] 汇总：" + "，".join(f"{s}={counts.get(s, 0)}" for s in STATUS_ORDER))

    meta = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ratio": ratio,
        "seed": args.seed,
        "python": sys.version.split()[0],
    }
    markdown = build_markdown(results, meta)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(markdown, encoding="utf-8")
        print(f"[regression] Markdown 报告已写入 {args.md}")
    else:
        print("\n" + markdown)

    if args.write_baseline:
        payload = {**meta, "counts": dict(counts), "results": [r.as_dict() for r in results]}
        args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
        args.write_baseline.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[regression] 基线已写入 {args.write_baseline}")

    if args.baseline:
        regressions = compare_baseline(results, args.baseline)
        if regressions:
            print(f"[regression] 发现 {len(regressions)} 个回归：")
            for r in regressions:
                print(f"  - {r.name}: -> {r.status}（{r.reason}）")
            return 1
        print("[regression] 与基线对比，无新增回归。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
