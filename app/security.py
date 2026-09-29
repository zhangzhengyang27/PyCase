"""安全检查模块：在运行示例前识别潜在风险。

支持三级风险分级（HIGH / MEDIUM / LOW）和白名单机制，
避免常见安全操作（如 subprocess.run 无 shell=True）被误报为高风险。
"""

import ast
import enum
import fnmatch
import warnings
from dataclasses import dataclass, field
from pathlib import Path


class RiskLevel(enum.Enum):
    """风险等级。"""

    HIGH = "high"  # 可能直接造成系统破坏、代码执行、数据泄露
    MEDIUM = "medium"  # 需要用户配置或注意，通常不会直接造成破坏
    LOW = "low"  # 提示性信息，如 GUI 环境、占位符


@dataclass
class RiskItem:
    """单条风险记录。"""

    description: str
    level: RiskLevel
    category: str = ""  # 风险类别：network / database / system / file / env / gui / syntax


@dataclass
class SecurityReport:
    """安全检查结果。"""

    is_safe: bool = True
    risks: list[str] = field(default_factory=list)  # 向后兼容：风险描述列表
    risk_details: list[RiskItem] = field(default_factory=list)  # 带等级的风险详情
    needs_config: list[str] = field(default_factory=list)

    @property
    def max_risk_level(self) -> RiskLevel | None:
        """返回最高风险等级，无风险时返回 None。"""
        if not self.risk_details:
            return None
        order = {RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
        return max(self.risk_details, key=lambda r: order[r.level]).level

    @property
    def high_risks(self) -> list[str]:
        """高风险描述列表。"""
        return [r.description for r in self.risk_details if r.level == RiskLevel.HIGH]

    @property
    def medium_risks(self) -> list[str]:
        """中风险描述列表。"""
        return [r.description for r in self.risk_details if r.level == RiskLevel.MEDIUM]

    @property
    def low_risks(self) -> list[str]:
        """低风险描述列表。"""
        return [r.description for r in self.risk_details if r.level == RiskLevel.LOW]

    def add_risk(
        self,
        description: str,
        level: RiskLevel = RiskLevel.MEDIUM,
        category: str = "",
    ) -> None:
        """添加一条风险（自动去重）。"""
        if description not in self.risks:
            self.risks.append(description)
            self.risk_details.append(RiskItem(description=description, level=level, category=category))
        self.is_safe = False


def _is_delete_call(node: ast.AST) -> tuple[bool, RiskLevel]:
    """判断是否为文件/目录删除操作，返回 (是否删除, 风险等级)。

    - rmtree / delete：递归删除，风险高
    - remove / unlink / rmdir：单文件/空目录删除，中风险
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        attr = node.func.attr
        if attr in ("rmtree", "delete"):
            return True, RiskLevel.HIGH
        if attr in ("remove", "unlink", "rmdir"):
            return True, RiskLevel.MEDIUM
    return False, RiskLevel.LOW


def _is_system_call(node: ast.AST, sp_names: set[str] | None = None) -> tuple[bool, RiskLevel, str]:
    """判断是否为系统命令调用，返回 (是否系统调用, 风险等级, 描述)。

    风险分级：
    - eval / exec：任意代码执行，高风险
    - os.system / os.popen：shell 命令执行，高风险
    - subprocess.run / subprocess.call / subprocess.Popen 等：
      - 含 shell=True：高风险（命令注入）
      - 无 shell=True：中风险（常见操作，通常安全）
    """
    if not isinstance(node, ast.Call):
        return False, RiskLevel.LOW, ""

    func = node.func

    # eval / exec（内置函数或属性调用）
    if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
        return True, RiskLevel.HIGH, f"任意代码执行：{func.id}()"

    if isinstance(func, ast.Attribute):
        attr = func.attr

        # os.system / os.popen
        if attr in ("system", "popen"):
            return True, RiskLevel.HIGH, f"系统命令执行：{attr}()"

        # eval / exec 作为属性调用
        if attr in ("eval", "exec"):
            return True, RiskLevel.HIGH, f"任意代码执行：{attr}()"

        # subprocess 系列：只在接收者确实是 subprocess（或其别名/from-import 名）时才判
        if attr in ("run", "call", "Popen", "check_call", "check_output") and _attr_root_name(func.value) in (sp_names or {"subprocess"}):
            # 检查是否有 shell=True
            has_shell_true = any(
                kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in node.keywords
            )
            if has_shell_true:
                return True, RiskLevel.HIGH, f"subprocess.{attr}(shell=True)：存在命令注入风险"
            return True, RiskLevel.MEDIUM, f"subprocess.{attr}()：子进程调用（无 shell=True）"

    return False, RiskLevel.LOW, ""


def subprocess_names(tree: ast.AST) -> set[str]:
    """该文件里绑定到 subprocess 模块的名字集合（含 ``import subprocess as sp``）。

    属性名（run/call/Popen…）本身不足以判定：``asyncio.run()``、用户对象上的
    ``loop.run()`` 都不是子进程调用，按属性名一律当 subprocess 会误报（G3）。
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "subprocess":
                    names.add(alias.asname or "subprocess")
    return names


def _attr_root_name(node: ast.AST) -> str | None:
    """取 ``a.b.c`` 的最左侧名字（a）。非 Name 根返回 None。"""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _has_import(tree: ast.AST, names: set[str]) -> bool:
    """检查 AST 中是否导入了指定模块名集合中的任意一个。"""
    return any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and any(alias.name.split(".")[0] in names for alias in node.names)
        for node in ast.walk(tree)
    )


class SecurityChecker:
    """静态分析 Python 代码中的潜在风险。

    基于 AST 的静态扫描，用于在不执行代码的前提下识别常见风险
    （网络访问、数据库操作、文件删除、系统命令、GUI 主循环、敏感信息等）。

    支持三级风险分级和白名单机制：
    - HIGH：可能直接造成系统破坏、代码执行、数据泄露
    - MEDIUM：需要用户配置或注意，通常不会直接造成破坏
    - LOW：提示性信息，如 GUI 环境、占位符

    白名单可通过构造参数或 check() 方法传入，支持精确 ID 和 glob 模式匹配。

    已知盲区（仅作静态扫描，无法覆盖所有情况）：
    - 通过变量、反射或别名间接调用危险函数（如 ``f = os.system; f(...)``）；
    - ``os.popen``、``__import__``、``importlib.import_module`` 等动态导入/调用；
    - 运行时拼接的命令字符串（命令注入）；
    - 依赖或第三方库内部的危险行为。
    若需要更强的审计，建议结合 bandit 等专业工具。
    """

    RISK_NETWORK = "网络请求（requests / urllib / selenium / scrapy）"
    RISK_DATABASE = "数据库连接（pymysql / sqlalchemy / pymongo / redis）"
    RISK_FILE_DELETE = "文件或目录删除操作"
    RISK_SYSTEM_CALL = "系统命令调用（os.system / subprocess / eval / exec）"
    RISK_SENSITIVE_ENV = "读取敏感环境变量或配置文件"
    RISK_GUI_LOOP = "GUI 主循环（tkinter / pygame）可能无法在嵌套环境中运行"

    def __init__(
        self,
        whitelist_ids: set[str] | None = None,
        whitelist_patterns: list[str] | None = None,
    ) -> None:
        """初始化安全检查器。

        Args:
            whitelist_ids: 安全示例 ID 集合，匹配时跳过检查直接返回安全报告。
            whitelist_patterns: 安全示例 ID 的 glob 模式列表（如 "pil_*", "dataviz_*"）。
        """
        self.whitelist_ids = whitelist_ids or set()
        self.whitelist_patterns = whitelist_patterns or []

    def is_whitelisted(self, example_id: str | None) -> bool:
        """检查示例 ID 是否在白名单中。"""
        if not example_id:
            return False
        if example_id in self.whitelist_ids:
            return True
        return any(fnmatch.fnmatch(example_id, pattern) for pattern in self.whitelist_patterns)

    def check(
        self,
        file_path: Path,
        example_id: str | None = None,
        *,
        content: str | None = None,
        tree: ast.AST | None = None,
    ) -> SecurityReport:
        """检查指定 Python 文件的安全风险。

        Args:
            file_path: 要检查的 Python 文件路径。
            example_id: 示例 ID（用于白名单匹配）。
            content/tree: 调用方已读取的源码与 AST（质量评分路径复用，
                避免同一文件重复读盘与 parse）；缺省时自行读取解析。
        """
        # 白名单匹配：直接返回安全报告
        if self.is_whitelisted(example_id):
            report = SecurityReport()
            report.needs_config.append(f"示例 {example_id} 已在白名单中，跳过安全扫描")
            return report

        report = SecurityReport()

        if content is None or tree is None:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    tree = ast.parse(content)
            except SyntaxError as e:
                report.add_risk(f"代码存在语法错误：{e}", RiskLevel.HIGH, "syntax")
                return report
            except OSError as e:
                report.add_risk(f"无法读取文件：{e}", RiskLevel.HIGH, "syntax")
                return report

        # 网络请求检测（中风险：需要网络权限和配置）
        if _has_import(tree, {"requests", "urllib", "selenium", "scrapy", "requests_html"}):
            report.add_risk(self.RISK_NETWORK, RiskLevel.MEDIUM, "network")
            report.needs_config.append("网络请求可能需要代理、Cookie、User-Agent 或 API Key")

        # 数据库检测（中风险：需要连接配置）
        if _has_import(tree, {"pymysql", "mysql", "sqlalchemy", "pymongo", "redis", "sqlite3"}):
            report.add_risk(self.RISK_DATABASE, RiskLevel.MEDIUM, "database")
            report.needs_config.append("数据库连接需要主机、端口、用户名、密码等配置")

        # GUI / 游戏循环检测（低风险：仅环境提示）
        if _has_import(tree, {"tkinter", "pygame", "PyQt5", "PyQt6", "PySide6"}):
            report.add_risk(self.RISK_GUI_LOOP, RiskLevel.LOW, "gui")
            report.needs_config.append("GUI 程序建议在独立终端运行，桌面应用中可能无法正常显示")

        # 敏感环境变量检测（中风险：可能读取密钥）
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in (
                    "getenv",
                    "getenvb",
                    "environ",
                ):
                    report.add_risk(self.RISK_SENSITIVE_ENV, RiskLevel.MEDIUM, "env")
                    break

        # 文件删除和系统调用检测（按操作类型分级）
        _sp_names = subprocess_names(tree)
        for node in ast.walk(tree):
            is_delete, delete_level = _is_delete_call(node)
            if is_delete:
                report.add_risk(self.RISK_FILE_DELETE, delete_level, "file")
            is_sys, sys_level, sys_desc = _is_system_call(node, _sp_names)
            if is_sys:
                report.add_risk(sys_desc, sys_level, "system")

        # 常见敏感占位符检测（低风险：仅提示需要替换）
        sensitive_patterns = [
            "YOUR_API_KEY",
            "YOUR_PASSWORD",
            "YOUR_USERNAME",
            "YOUR_SECRET",
            "YOUR_TOKEN",
        ]
        for pattern in sensitive_patterns:
            if pattern in content:
                report.needs_config.append(f"代码中包含占位符 {pattern}，运行前需要替换")

        return report
