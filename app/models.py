"""数据模型定义。"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExampleItem:
    """表示一个 Python 示例或目录节点。"""

    name: str
    path: Path
    is_dir: bool
    category: str  # 'topics', 'tools', 'projects', 'root', 'favorites'
    parent: Optional["ExampleItem"] = None
    children: list["ExampleItem"] = field(default_factory=list)
    readme_path: Path | None = None
    tags: list[str] = field(default_factory=list)
    # 质量评分：None 表示尚未计算（惰性计算，首次需要时才做 AST 解析）
    quality_score: int | None = None
    repo_root: Path | None = None
    # 数据源标识：'filesystem'（磁盘真实 .py）或 'json'（JSON 示例集）
    source: str = "filesystem"
    # source='json' 时保存内联代码（用于回写 JSON）；filesystem 来源为 None
    code: str | None = None
    json_id: str | None = None
    json_file: Path | None = None
    # 示例描述（来自 JSON 的 description 字段）
    description: str | None = None
    # 示例标题（来自 JSON 的 title 字段，为空时回退到 name 或 README）
    json_title: str | None = None
    # 原始仓库内相对目录（JSON 条目的 dir 字段，如 'tools/utility-crawlers'）；
    # 文件系统来源与用户导入集合为 None。工具箱页面用它做工具项目分组。
    source_dir: str | None = None
    # 运行该示例时需要的额外 sys.path（原始目录及其祖先目录，用于解析兄弟/包导入）
    run_pythonpath: list[str] = field(default_factory=list)

    @property
    def relative_path(self) -> str:
        """返回相对于仓库根目录的路径。"""
        # 优先使用索引时记录的仓库根，最稳健
        if self.repo_root is not None:
            try:
                return self.path.relative_to(self.repo_root).as_posix()
            except ValueError:
                pass
        # 兜底：从路径向上查找 topics/tools/projects 目录反推仓库根
        current = self.path
        while current.parent.name not in ("", "/"):
            if current.parent.name in ("topics", "tools", "projects"):
                try:
                    return self.path.relative_to(current.parent.parent).as_posix()
                except ValueError:
                    break
            current = current.parent
        return self.path.as_posix()

    @property
    def title(self) -> str:
        """返回用于展示的标题。"""
        # 优先使用 JSON 中存储的 title
        if self.json_title:
            return self.json_title
        # 其次从 README 中提取
        if self.readme_path and self.readme_path.exists():
            content = self.readme_path.read_text(encoding="utf-8", errors="ignore")
            first_line = content.strip().splitlines()[0] if content.strip() else ""
            if first_line.startswith("#"):
                return first_line.lstrip("#").strip()
        return self.name

    @property
    def readme_summary(self) -> str:
        """返回 README 的摘要内容。"""
        if not self.readme_path or not self.readme_path.exists():
            return ""
        content = self.readme_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.strip().splitlines()
        # 过滤掉标题，取前 10 行非空内容
        summary_lines = []
        for line in lines[1:]:
            if line.strip():
                summary_lines.append(line.strip())
            if len(summary_lines) >= 10:
                break
        return "\n".join(summary_lines)

    def __repr__(self) -> str:
        return (
            f"ExampleItem(name={self.name!r}, path={self.path!r}, is_dir={self.is_dir})"
        )
