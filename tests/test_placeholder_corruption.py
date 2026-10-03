"""示例语料占位符损坏守卫（2026-10-02 数据修复收口）。

背景：生成器曾产出一批「占位符不生效」的损坏示例，两种形态——
  ① f-string 内 {{expr}}：合法转义语义，运行输出字面 {expr}（用户逐一手修）；
  ② 普通字符串里 {var}：缺 f 前缀，print 输出字面 {var}（用户截图 date-diff 即此）。
本守卫钉住「运行时级损坏为零」：非 docstring 的字符串常量里出现「变量形态的
占位符且名字在模块作用域内可解析」即红。docstring 的 {title}/{desc} 是生成器
文案模板（改 f 会 NameError），属已知化妆品级遗留，不在本守卫口径内。
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOTS = ["json_examples", "topics", "tools", "projects", "examples_assets"]
PLACEHOLDER = re.compile(r"\{([A-Za-z_][\w\.\(\)\[\]]*(\s*[\+\-\*/%]\s*[\w\.\(\)\[\]]+)*)\}")
VARLIKE = re.compile(r"^[A-Za-z_]\w*(\.\w+|\[[^\]]+\])*$")


def _module_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for a in n.args.args + n.args.kwonlyargs + n.args.posonlyargs:
                    names.add(a.arg)
        elif isinstance(n, ast.Name):
            names.add(n.id)
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                names.add(a.asname or a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                names.add((a.asname or a.name).split(".")[0])
    return names


def _runtime_corruptions(src: str, tree: ast.Module) -> list[str]:
    names = _module_names(tree)
    doc_nodes = {
        n.body[0].value
        for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and n.body
        and isinstance(n.body[0], ast.Expr)
        and isinstance(n.body[0].value, ast.Constant)
    }
    hits: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        text = node.value
        if node in doc_nodes or "$" in text:  # docstring 模板 / LaTeX mathtext 豁免
            continue
        for m in PLACEHOLDER.finditer(text):
            ph = m.group(1)
            if not VARLIKE.match(ph):
                continue
            root_name = ph.split(".")[0].split("[")[0]
            if root_name in names or ph.startswith(("self.", "cls.")):
                hits.append(ph)
    return hits


def test_corpus_has_no_runtime_placeholder_corruption():
    """语料中不得存在「会被当字面量打印的变量占位符」（占位符损坏 ①② 的回归网）。"""
    bad: list[str] = []
    scanned = 0
    for root in ROOTS:
        for p in (ROOT / root).rglob("*.py"):
            if ".backup" in p.parts:
                continue
            try:
                src = p.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            scanned += 1
            for ph in _runtime_corruptions(src, tree):
                bad.append(f"{p.relative_to(ROOT)}: {ph}")
    assert scanned > 450, f"语料扫描量异常（{scanned}），检查 ROOTS 是否仍指向真相源"
    assert not bad, f"发现 {len(bad)} 处占位符损坏（输出会是字面量而非值）:\n" + "\n".join(bad[:20])
