"""示例质量评分器。"""

import ast
import functools
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from .models import ExampleItem
from .security import SecurityChecker
from .utils import is_python_file


@dataclass
class QualityReport:
    """示例质量报告。"""

    score: int = 0  # 0-100
    runnability: int = 0
    readme_completeness: int = 0
    dependency_clarity: int = 0
    security_risk: int = 0
    code_style: int = 0
    documentation: int = 0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class QualityScorer:
    """对 Python 示例进行多维度质量评分。"""

    def __init__(self) -> None:
        self.security_checker = SecurityChecker()

    def score(self, item: ExampleItem) -> QualityReport:
        """计算示例的质量评分。"""
        report = QualityReport()

        if item.is_dir:
            return report

        if not is_python_file(item.path):
            return report

        # 单次读盘 + 单次 ast.parse，六个子检查共享结果。
        # （旧实现各子检查独立读盘/parse，1349 例首轮评分累计约 5000 次 parse）
        content: str | None = None
        tree: ast.Module | None = None
        syntax_err: SyntaxError | None = None
        try:
            content = item.path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = None
        if content is not None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    tree = ast.parse(content)
            except SyntaxError as e:
                syntax_err = e

        # 1. 可运行性（30%）：语法检查
        report.runnability = self._check_runnability(content, tree, syntax_err)

        # 2. README 完整性（20%）
        report.readme_completeness = self._check_readme(item)

        # 3. 依赖明确性（15%）
        report.dependency_clarity = self._check_dependencies(item.path, content, tree)

        # 4. 安全风险（15%）
        report.security_risk = self._check_security(
            item.path, content=content, tree=tree
        )

        # 5. 代码规范（10%）
        report.code_style = self._check_code_style(content)

        # 6. 文档注释（10%）
        report.documentation = self._check_documentation(tree)

        # 加权计算总分
        weights = {
            "runnability": 0.30,
            "readme_completeness": 0.20,
            "dependency_clarity": 0.15,
            "security_risk": 0.15,
            "code_style": 0.10,
            "documentation": 0.10,
        }
        report.score = int(
            report.runnability * weights["runnability"]
            + report.readme_completeness * weights["readme_completeness"]
            + report.dependency_clarity * weights["dependency_clarity"]
            + report.security_risk * weights["security_risk"]
            + report.code_style * weights["code_style"]
            + report.documentation * weights["documentation"]
        )

        self._generate_feedback(report)
        return report

    def _check_runnability(
        self,
        content: str | None,
        tree: ast.Module | None,
        syntax_err: SyntaxError | None,
    ) -> int:
        """检查代码是否能通过语法编译。"""
        if content is None:
            return 0
        if tree is not None:
            return 100
        return max(0, 100 - len(str(syntax_err).splitlines()) * 10)

    def _check_readme(self, item: ExampleItem) -> int:
        """检查 README 的完整性。"""
        if not item.readme_path or not item.readme_path.exists():
            return 0

        try:
            content = item.readme_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return 0

        score = 30  # 存在 README
        stripped = content.strip()

        if stripped:
            score += 20  # 非空

        # 检查是否有标题
        if any(line.strip().startswith("#") for line in stripped.splitlines()):
            score += 20

        # 检查是否有说明文字（标题以外的内容）
        non_title_lines = [
            line for line in stripped.splitlines() if not line.strip().startswith("#")
        ]
        if any(line.strip() for line in non_title_lines):
            score += 30

        return min(100, score)

    def _find_dependency_file(self, file_path: Path) -> Path | None:
        """从文件所在目录开始，向上逐级查找最近的依赖声明文件。

        兼容嵌套子目录中的示例（其依赖声明在更上层目录）。
        限制查找深度，避免扫描整个文件系统。
        """
        current = file_path.parent
        for _ in range(10):
            for name in ("requirements.txt", "pyproject.toml", "setup.py"):
                candidate = current / name
                if candidate.exists():
                    return candidate
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    def _check_dependencies(
        self, file_path: Path, content: str | None, tree: ast.Module | None
    ) -> int:
        """检查依赖是否明确。"""
        dep_file = self._find_dependency_file(file_path)
        if dep_file is not None:
            if dep_file.name in ("requirements.txt", "pyproject.toml"):
                return 100
            return 80  # setup.py

        # 如果没有依赖文件，检查是否有第三方导入
        if content is None or tree is None:
            return 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module not in self._stdlib_modules():
                        return 20  # 有第三方依赖但没有依赖文件
        return 80  # 没有第三方依赖，不需要依赖文件

    def _check_security(
        self,
        file_path: Path,
        *,
        content: str | None = None,
        tree: ast.Module | None = None,
    ) -> int:
        """根据安全扫描结果评分。"""
        report = self.security_checker.check(file_path, content=content, tree=tree)
        risk_count = len(report.risks)
        if risk_count == 0:
            return 100
        if risk_count == 1:
            return 70
        if risk_count <= 3:
            return 40
        return 10

    def _check_code_style(self, content: str | None) -> int:
        """简单的代码规范检查。"""
        if content is None:
            return 0

        issues = 0
        lines = content.splitlines()
        for line in lines:
            # 行长度检查
            if len(line) > 120:
                issues += 1
            # 尾随空格
            if line.endswith(" ") or line.endswith("\t"):
                issues += 1

        # 空文件或极短文件
        if not lines:
            return 0

        return max(0, 100 - min(issues * 5, 100))

    def _check_documentation(self, tree: ast.Module | None) -> int:
        """检查函数和类是否有文档字符串。"""
        if tree is None:
            return 0

        total = 0
        documented = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                total += 1
                if ast.get_docstring(node):
                    documented += 1

        if total == 0:
            return 60  # 没有函数/类，给基础分

        return int((documented / total) * 100)

    def _generate_feedback(self, report: QualityReport) -> None:
        """根据评分生成问题和建议。"""
        report.issues = []
        report.suggestions = []

        if report.runnability < 100:
            report.issues.append("代码存在语法错误，可能无法运行")
            report.suggestions.append("修复语法错误后再运行")

        if report.readme_completeness < 60:
            report.issues.append("README 不完整或缺失")
            report.suggestions.append("补充 README.md，包含标题和功能说明")

        if report.dependency_clarity < 60:
            report.issues.append("依赖声明不明确")
            report.suggestions.append("添加 requirements.txt 或 pyproject.toml")

        if report.security_risk < 80:
            report.issues.append("代码存在安全风险")
            report.suggestions.append("审查网络、系统调用、文件删除等敏感操作")

        if report.code_style < 80:
            report.issues.append("代码风格有待改进")
            report.suggestions.append("控制行长度在 120 字符内，去除尾随空格")

        if report.documentation < 60:
            report.issues.append("函数/类缺少文档字符串")
            report.suggestions.append("为公开函数和类添加 docstring")

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _stdlib_modules() -> frozenset[str]:
        """返回标准库模块名集合（Python 3.10+ 使用 sys.stdlib_module_names）。"""
        if hasattr(sys, "stdlib_module_names"):
            return frozenset(sys.stdlib_module_names)
        # 旧版本 Python 回退到常见标准库集合
        return frozenset(
            {
                "abc",
                "argparse",
                "ast",
                "asyncio",
                "builtins",
                "collections",
                "contextlib",
                "copy",
                "csv",
                "datetime",
                "decimal",
                "enum",
                "fnmatch",
                "functools",
                "glob",
                "hashlib",
                "heapq",
                "importlib",
                "inspect",
                "io",
                "itertools",
                "json",
                "logging",
                "math",
                "os",
                "pathlib",
                "pickle",
                "random",
                "re",
                "shutil",
                "socket",
                "sqlite3",
                "statistics",
                "string",
                "subprocess",
                "sys",
                "tempfile",
                "threading",
                "time",
                "traceback",
                "typing",
                "unittest",
                "urllib",
                "uuid",
                "warnings",
                "xml",
                "zipfile",
            }
        )
