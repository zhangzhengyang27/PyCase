#!/usr/bin/env python3
"""为 json_examples 缺失 description 的示例补齐描述（v0.7 数据补全）。

多级策略（与 examples.json 现有短句风格对齐：一句中文、以句号结尾）：
  1. 模块 docstring（ast 提取，语法失败回退正则）；
  2. 文件头部连续 # 注释块（排除 shebang/编码/作者元数据/分隔线）；
  3. 首个函数/类的 docstring；
  4. 正文首条有效注释（含中文或长度足够、非元数据/分隔线）；
  5. 按导入库合成（pandas/matplotlib/爬虫/GUI 等）；
  6. 按标签翻译合成（algorithms→算法 等）；
  7. 兜底「Python 代码示例。」。

只填空，不覆盖已有描述；幂等（重复运行零改动）。默认 dry-run，--apply 才写回。
用法：python scripts/gen_descriptions.py [--apply]
"""
from __future__ import annotations

import ast
import json
import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "json_examples"
MAX_LEN = 110

# 元数据/噪声注释（作者、日期、版权等不构成描述）
_META_RE = re.compile(
    r"@author|@date|@time|@file|@contact|copyright|版权|作者|创建时间|更新时间|license"
    r"|^-\*-|^#!|^coding\s*[:=]|coding\s*[:=]\s*\w",
    re.I,
)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# 第三方库 → 中文短语（覆盖 migrated 集合实际出现的库）
LIB_PHRASES: list[tuple[str, str]] = [
    (r"\bmatplotlib\b|\bpyplot\b", "matplotlib 绘图"),
    (r"\bpandas\b", "pandas 数据处理"),
    (r"\bnumpy\b", "numpy 数值计算"),
    (r"\bPIL\b|\bPillow\b", "Pillow 图像处理"),
    (r"\bcv2\b", "OpenCV 视觉处理"),
    (r"\bturtle\b", "turtle 绘图"),
    (r"\bpygame\b", "pygame 游戏开发"),
    (r"\brequests\b", "requests HTTP 请求"),
    (r"\bscrapy\b", "Scrapy 爬虫"),
    (r"\bbs4\b|BeautifulSoup", "BeautifulSoup 网页解析"),
    (r"\blxml\b", "lxml 文档解析"),
    (r"\bflask\b", "Flask Web 应用"),
    (r"\bdjango\b", "Django Web 应用"),
    (r"\bopenpyxl\b|\bxlrd\b|\bxlsxwriter\b", "Excel 表格处理"),
    (r"\bfrom docx\b|\bimport docx\b", "Word 文档处理"),
    (r"\bPyPDF2\b|\bpypdf\b|\bpdfplumber\b", "PDF 文档处理"),
    (r"\bsqlite3\b", "SQLite 数据库"),
    (r"\bsqlalchemy\b", "SQLAlchemy 数据库"),
    (r"\bpymysql\b|\bpsycopg2\b", "数据库操作"),
    (r"\btkinter\b", "tkinter 桌面界面"),
    (r"\bseaborn\b", "seaborn 统计可视化"),
    (r"\bpyecharts\b", "pyecharts 可视化"),
    (r"\bselenium\b", "Selenium 浏览器自动化"),
    (r"\bparamiko\b", "SSH 远程操作"),
    (r"\bsmtplib\b", "邮件发送"),
    (r"\bthreading\b|\basyncio\b|\bconcurrent\b", "并发编程"),
    (r"\bsocket\b", "网络套接字编程"),
    (r"\bre\b", "正则表达式"),
    (r"\bjson\b", "JSON 数据处理"),
    (r"\bcsv\b", "CSV 数据处理"),
    (r"\bdatetime\b", "日期时间处理"),
    (r"\bpathlib\b|\bshutil\b|\bglob\b", "文件与目录操作"),
    (r"\bzipfile\b|\btarfile\b", "压缩包处理"),
    (r"\bsubprocess\b", "子进程调用"),
    (r"\bhashlib\b", "哈希计算"),
    (r"\bredis\b", "Redis 操作"),
]

# 标签 → 中文（正文合成用）
TAG_PHRASES = {
    "algorithms": "算法",
    "language-fundamentals": "语言基础",
    "language-advanced": "语言进阶",
    "python-basics": "Python 基础",
    "python-advanced": "Python 进阶",
    "python-core-concepts": "Python 核心概念",
    "web-crawling": "网络爬虫",
    "web-development": "Web 开发",
    "web": "Web 开发",
    "office-automation": "办公自动化",
    "data-analysis": "数据分析",
    "automation-testing": "自动化测试",
    "excel-operations": "Excel 操作",
    "productivity-course": "效率工具",
    "scrapy-projects": "Scrapy 项目",
    "utility-crawlers": "实用爬虫",
    "network": "网络编程",
    "并发": "并发编程",
    "网络": "网络编程",
    "导出": "数据导出",
    "命令行": "命令行",
}


def _clip(text: str) -> str:
    """压缩空白并截断到长度上限（尽量在句末截断）。"""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= MAX_LEN:
        return text
    cut = text[:MAX_LEN]
    for punct in ("。", "；", "！", "？", ".", ";"):
        i = cut.rfind(punct)
        if i >= MAX_LEN * 0.5:
            return cut[: i + 1]
    return cut.rstrip("，,、：: ") + "…"


def _ends_sentence(text: str) -> bool:
    return text.endswith(("。", "！", "？", "!", "?", ".", "…"))


# 看起来是代码而非自然语言的注释（注释掉的代码行、压缩 JS 等）
_CODEISH_RE = re.compile(
    r"\w+\(\)[.:]|=>|&&|\.concat\(|\bself\.\b|\bprint\(|\brange\(|\bdef \b|\breturn\b"
    r"|\bfor \b|\bif \b|\bwhile \b|\bimport \b|\bfrom \b|\bclass \b|\btry:\b|\belif\b"
)


def _parse(code: str) -> ast.Module | None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 示例代码里的无效转义等 SyntaxWarning 不入耳
        try:
            return ast.parse(code)
        except (SyntaxError, ValueError, RecursionError):
            m = re.match(r'\s*(?:"""|\'\'\')([\s\S]*?)("""|\'\'\')', code)
            return None if m is None else "regex-docstring-only"  # type: ignore[return-value]


def _module_docstring(code: str) -> str:
    tree = _parse(code)
    if tree is None:
        return ""
    if tree == "regex-docstring-only":  # type: ignore[comparison-overlap]
        m = re.match(r'\s*(?:"""|\'\'\')([\s\S]*?)("""|\'\'\')', code)
        return m.group(1).strip() if m else ""
    return (ast.get_docstring(tree) or "").strip()


def _valid_comment(body: str) -> bool:
    """注释行是否值得作为描述素材。"""
    if not body or _META_RE.search(body):
        return False
    if re.fullmatch(r"[-=\*\#~\s\d.,;:！？。，；]+", body):
        return False
    # 描述必须以自然语言开头：前 12 字符内须出现中文（排除元组输出、
    # 「代码在前中文在后」的被注释代码行）
    if _CJK_RE.search(body) and not _CJK_RE.search(body[:12]):
        return False
    # 赋值调用（thresh = cv2.threshold(...)）不是描述
    if re.search(r"\w+\s*=\s*\w+\(", body):
        return False
    if _CJK_RE.search(body):
        if _CODEISH_RE.search(body):
            return False
        return len(body) >= 4
    if len(body) < 12:
        return False
    # 纯英文：排除命令行/安装提示与含代码符号的行
    if re.match(r"^(pip|npm|install|cd|git|python|sudo|usage|note|todo)\b", body, re.I):
        return False
    return not _CODEISH_RE.search(body) and not re.search(r"[(){};=]", body)


def _has_param_junk(text: str) -> bool:
    """docstring 片段里残留的 :param/:return 标记不算描述。"""
    return ":param" in text or ":return" in text or ":rtype" in text


def extract_header_comments(code: str) -> str:
    """首个语句前的连续 # 注释块（跳过 shebang / 编码 / 元数据 / 分隔线）。"""
    lines: list[str] = []
    for line in code.splitlines():
        s = line.strip()
        if not s:
            if lines:
                break
            continue
        if s.startswith("#!"):
            continue
        if s.startswith("#"):
            body = s.lstrip("#").strip()
            if "coding" in body[:20] or not _valid_comment(body):
                continue
            lines.append(body)
            continue
        break
    return " ".join(lines)


def _func_docstring(code: str) -> str:
    tree = _parse(code)
    if not tree or tree == "regex-docstring-only":  # type: ignore[comparison-overlap]
        return ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc and len(doc.strip()) >= 8:
                return doc.strip().split("\n")[0]
    return ""


def _body_comment(code: str) -> str:
    for line in code.splitlines():
        s = line.strip()
        if s.startswith("#") and not s.startswith("#!"):
            body = s.lstrip("#").strip()
            if _valid_comment(body):
                return body
    return ""


def synthesize(code: str, name: str, tags: list[str]) -> str:
    phrases: list[str] = []
    for pattern, phrase in LIB_PHRASES:
        if re.search(pattern, code) and phrase not in phrases:
            phrases.append(phrase)
        if len(phrases) >= 3:
            break
    if phrases:
        head = "、".join(phrases[:2]) + (" 等综合运用" if len(phrases) > 2 else "")
        return _clip(f"演示 {head} 的 Python 示例。")
    for tag in tags:
        if tag in TAG_PHRASES:
            label = TAG_PHRASES[tag]
            if "Python" in label:
                return f"{label}练习示例。"
            return f"{label}方向的 Python 练习示例。"
    return "Python 代码示例。"


# ---------------------------------------------------------------------------
# 第二遍升级：为套话类描述（标签兜底 / 单一「演示…」模板）挖掘逐文件信号，
# 让同标签的 example01-N 系列互相可区分。
# 信号优先级：CJK 字符串字面量（题目/提示语句）→ 顶层函数与类名 → 结构特征。
# ---------------------------------------------------------------------------

def _string_literals(code: str) -> list[str]:
    """正文中的 CJK 字符串字面量（教程脚本常在 print/赋值里写题目语句）。

    排除交互提示语（请选择/请输入/正在…）——它们是运行时 UI 文案，不是描述。"""
    tree = _parse(code)
    if not tree or tree == "regex-docstring-only":  # type: ignore[comparison-overlap]
        return []
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if not _CJK_RE.search(v) or len(v) < 12:
                continue
            if not _CJK_RE.search(v[:12]):
                continue
            if re.match(r"^(请|正在|加载|错误|失败|成功|警告|提示|欢迎|菜单|第[一二三四五六七八九十\d]+[、.章])", v):
                continue
            if _has_param_junk(v):
                continue
            out.append(v)
    return out


def _top_defs(code: str) -> tuple[list[str], list[str]]:
    """顶层函数名与类名（main 视为入口不算特征；单双字符名信息量为零，剔除）。"""
    tree = _parse(code)
    if not tree or tree == "regex-docstring-only":  # type: ignore[comparison-overlap]
        return [], []
    funcs: list[str] = []
    classes: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != "main" and len(node.name) >= 3:
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef) and len(node.name) >= 3:
            classes.append(node.name)
    return funcs, classes


def _has_recursion(code: str) -> bool:
    tree = _parse(code)
    if not tree or tree == "regex-docstring-only":  # type: ignore[comparison-overlap]
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == node.name:
                    return True
    return False


def _structural_hints(code: str) -> list[str]:
    hints: list[str] = []
    if re.search(r"\bsorted\(|\.sort\(", code):
        hints.append("排序处理")
    if re.search(r"\bopen\(", code):
        hints.append("文件读写")
    if re.search(r"\binput\(", code):
        hints.append("交互输入")
    if _has_recursion(code):
        hints.append("递归实现")
    return hints


def _first_lib(code: str) -> str:
    for pattern, phrase in LIB_PHRASES:
        if re.search(pattern, code):
            return phrase
    return ""


def _func_phrase(funcs: list[str]) -> str:
    if len(funcs) == 1:
        return f"定义 {funcs[0]} 函数"
    if len(funcs) == 2:
        return f"定义 {funcs[0]}、{funcs[1]} 函数"
    return f"定义 {funcs[0]}、{funcs[1]} 等 {len(funcs)} 个函数"


def build_rich(item: dict) -> str | None:
    """为套话描述生成更有信息量的替代；无信号时返回 None（保留原描述）。"""
    code = item.get("code") or ""

    literals = _string_literals(code)
    if literals:
        text = _clip(literals[0])
        if len(text) >= 10 and not _has_param_junk(text):
            return text if _ends_sentence(text) else text + "。"

    funcs, classes = _top_defs(code)
    lib = _first_lib(code)
    hints = _structural_hints(code)
    if funcs:
        parts = [_func_phrase(funcs)]
        if classes:
            parts.append(f"含 {classes[0]} 类")
        if lib:
            parts.append(f"演示 {lib}")
        elif hints:
            parts.append("含 " + "、".join(hints[:2]))
        return "，".join(parts) + "。"
    if classes:
        text = f"实现 {classes[0]} 类"
        if lib:
            text += f"，演示 {lib}"
        elif hints:
            text += "，含 " + "、".join(hints[:2])
        return text + "。"
    if lib and hints:
        return f"演示 {lib}，含 " + "、".join(hints[:2]) + "。"
    return None


def is_formulaic(desc: str) -> bool:
    """是否属于套话类描述（第二遍升级的对象）。"""
    return (
        desc == "Python 代码示例。"
        or desc.endswith("练习示例。")
        or bool(re.match(r"^演示 .+ 的 Python 示例。$", desc))
    )


def build_description(item: dict) -> str:
    code = item.get("code") or ""
    name = item.get("name") or ""
    tags = item.get("tags") or []

    doc = _module_docstring(code)
    if doc:
        first_para = re.split(r"\n\s*\n", doc)[0]
        text = _clip(first_para)
        if len(text) >= 8:
            return text if _ends_sentence(text) else text + "。"

    for candidate in (extract_header_comments(code), _func_docstring(code), _body_comment(code)):
        if candidate and len(candidate) >= 8 and not _has_param_junk(candidate):
            text = _clip(candidate)
            if len(text) < 8 or _has_param_junk(text):
                continue
            return text if _ends_sentence(text) else text + "。"

    return synthesize(code, name, tags)


def main() -> int:
    apply = "--apply" in sys.argv
    upgrade = "--upgrade" in sys.argv
    grand: dict[str, int] = {"scanned": 0, "filled": 0, "doc": 0, "header": 0, "func": 0, "body": 0, "synth": 0}
    up: dict[str, int] = {"target": 0, "literal": 0, "defs": 0, "libhints": 0, "kept": 0}
    for path in sorted(JSON_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("examples") if isinstance(data, dict) else None
        if items is None:
            continue
        filled = 0
        upgraded = 0
        for it in items:
            grand["scanned"] += 1

            if upgrade:
                # 第二遍：只升级套话类描述。
                # 字面量/函数类信号 → 直接替换（价值在唯一性，不在长度）；
                # 库+结构信号 → 需比原描述更长才替换。
                current = (it.get("description") or "").strip()
                if not current or not is_formulaic(current):
                    continue
                up["target"] += 1
                rich = build_rich(it)
                if not rich:
                    up["kept"] += 1
                    continue
                code = it.get("code") or ""
                if _string_literals(code):
                    up["literal"] += 1
                elif _top_defs(code)[0] or _top_defs(code)[1]:
                    up["defs"] += 1
                elif len(rich) > len(current) + 4:
                    up["libhints"] += 1
                else:
                    up["kept"] += 1
                    continue
                upgraded += 1
                if apply:
                    it["description"] = rich
                continue

            if (it.get("description") or "").strip():
                continue
            desc = build_description(it)
            if len(desc) < 6:
                continue
            grand["filled"] += 1
            filled += 1
            if _module_docstring(it.get("code") or ""):
                grand["doc"] += 1
            elif extract_header_comments(it.get("code") or ""):
                grand["header"] += 1
            elif _func_docstring(it.get("code") or ""):
                grand["func"] += 1
            elif _body_comment(it.get("code") or ""):
                grand["body"] += 1
            else:
                grand["synth"] += 1
            if apply:
                it["description"] = desc

        changed = filled if not upgrade else upgraded
        if apply and changed:
            # 与 sidecar 写回格式一致：ensure_ascii=False, indent=2
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        label = "补" if not upgrade else "升级"
        print(f"{path.name}: {label} {changed}")

    if upgrade:
        print(f"套话目标 {up['target']}：字面量 {up['literal']} / 函数类 {up['defs']} / 库+结构 {up['libhints']} / 保留 {up['kept']}")
    else:
        print(
            f"合计 scanned={grand['scanned']} filled={grand['filled']} "
            f"(docstring={grand['doc']} 头注释={grand['header']} 函数doc={grand['func']} "
            f"正文注释={grand['body']} 合成={grand['synth']})"
        )
    if not apply:
        print("（dry-run，未写回；加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
