"""示例可运行性判定（派生数据，不落盘）。

run_status 与 quality_score / risk_high 同为惰性计算的派生数据，不写入 JSON：
- runnable       推定可运行（静态检查全部通过，不保证实跑成功）
- missing_deps   第三方 import 在共享 .venv 中不存在（运行必 ImportError）
- empty          空壳：去除 docstring 后无实际语句（或代码过短）
- broken         语法错误（无法 ast.parse，运行必 SyntaxError）
- risky          含 HIGH 风险操作（与高危徽章同源判定，可运行但有风险）

判定优先级：broken > empty > missing_deps > risky > runnable——
用户第一诉求是"能不能跑起来"，故缺依赖优先于风险提示。

缺依赖判定依赖共享 .venv 的模块索引（ModuleIndex）；索引不可用时跳过该维度
（宁可漏报不误报），状态落为 risky / runnable。
"""

import ast
import json
import subprocess
import sys
import warnings
from pathlib import Path

from .security import RiskLevel, SecurityChecker

RUNNABLE = "runnable"
MISSING_DEPS = "missing_deps"
EMPTY = "empty"
BROKEN = "broken"
RISKY = "risky"

# 状态 → 用户可读文案（前端徽章/详情页与指标报告共用）
STATUS_LABELS = {
    RUNNABLE: "可运行",
    MISSING_DEPS: "缺依赖",
    EMPTY: "空壳",
    BROKEN: "语法损坏",
    RISKY: "高危",
}

# 空壳阈值：去除 docstring 后有效代码不足该字符数视为空壳（与 audit_examples.py 口径一致）
MIN_MEANINGFUL_CHARS = 30

# 让共享 venv 解释器枚举自身可导入的顶层模块名（一次子进程，之后内存集合比对）。
# pkgutil.iter_modules 不枚举 PEP 420 命名空间包（无 __init__.py，如 mpl_toolkits），
# 需补扫 site-packages 等路径下的目录名，否则此类模块被误判缺依赖。
_LIST_MODULES_SNIPPET = """import json, os, pkgutil, sys
names = {m.name for m in pkgutil.iter_modules()}
for p in sys.path:
    if not p or not os.path.isdir(p):
        continue
    for n in os.listdir(p):
        if (
            n.isidentifier()
            and not n.startswith((".", "_"))
            and not n.endswith((".dist-info", ".egg-info"))
            and os.path.isdir(os.path.join(p, n))
        ):
            names.add(n)
json.dump(sorted(names), sys.stdout)
"""


def parse_code(code: str) -> ast.Module | None:
    """解析代码，语法错误返回 None（同时抑制示例代码常见的无效转义警告）。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return ast.parse(code)
        except SyntaxError:
            return None


def is_empty_body(tree: ast.Module, code: str) -> bool:
    """空壳判定：去除 docstring/纯常量表达式后无实际语句，或有效字符数过短。"""
    body = [n for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    return not body or len(code.strip()) < MIN_MEANINGFUL_CHARS


def _is_local_module(mod: str, directory: Path) -> bool:
    """mod 是否为 directory 内的本地模块/包（物化目录里已含兄弟文件与数据）。"""
    try:
        return (directory / f"{mod}.py").exists() or (directory / mod).is_dir()
    except OSError:
        return False


def third_party_imports(code: str, tree: ast.Module, local_dirs: list[Path]) -> set[str]:
    """顶层第三方 import 模块名（排除标准库与本地目录内可解析的模块）。"""
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    stdlib = set(sys.stdlib_module_names)
    return {
        m
        for m in mods
        if m not in stdlib and not any(_is_local_module(m, d) for d in local_dirs)
    }


class ModuleIndex:
    """共享 .venv 可导入顶层模块名索引。

    用目标解释器一次性枚举（iter_modules），此后每个示例的依赖判定都是
    内存集合差运算，无子进程开销。枚举失败时 available=False，
    调用方应跳过缺依赖维度（不误报）。
    """

    def __init__(self, python_exe: str | None = None, timeout: float = 60.0) -> None:
        self.available = False
        self._modules: frozenset[str] = frozenset()
        if python_exe:
            self._load(python_exe, timeout)

    def _load(self, python_exe: str, timeout: float) -> None:
        try:
            # -I 隔离模式：sys.path 不含 cwd/PYTHONPATH/用户目录，避免把
            # 仓库顶层目录（app/tools/projects/scripts/tests）误判为可导入模块
            proc = subprocess.run(
                [python_exe, "-I", "-c", _LIST_MODULES_SNIPPET],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if proc.returncode == 0:
                self._modules = frozenset(json.loads(proc.stdout))
                self.available = True
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
            self.available = False

    def missing_modules(self, mods: set[str]) -> set[str]:
        """mods 中在标准库与 .venv 里都不存在的模块名。索引不可用时返回空集。"""
        if not self.available:
            return set()
        stdlib = set(sys.stdlib_module_names)
        return {m for m in mods if m not in stdlib and m not in self._modules}

    def is_available(self, mod: str) -> bool:
        """单模块可用性谓词（导入器依赖猜测注入用）。

        索引不可用时返回 True（宁可少猜不误删，与 missing_modules 的保守口径一致）。
        """
        if not self.available:
            return True
        return mod in sys.stdlib_module_names or mod in self._modules


def compute_run_status(
    code: str,
    *,
    example_id: str | None = None,
    local_dirs: list[Path] | None = None,
    checker: SecurityChecker,
    module_index: ModuleIndex | None = None,
) -> str:
    """单示例可运行性判定（纯函数，不做缓存；ExampleStore 层负责缓存与失效）。"""
    code = code or ""
    if not code.strip():
        return EMPTY
    tree = parse_code(code)
    if tree is None:
        return BROKEN
    if is_empty_body(tree, code):
        return EMPTY
    if module_index is not None and module_index.available:
        mods = third_party_imports(code, tree, local_dirs or [])
        if module_index.missing_modules(mods):
            return MISSING_DEPS
    report = checker.check(Path("x.py"), example_id, content=code, tree=tree)
    if any(r.level == RiskLevel.HIGH for r in report.risk_details):
        return RISKY
    return RUNNABLE
