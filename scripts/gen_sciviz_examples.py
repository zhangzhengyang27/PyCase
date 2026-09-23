#!/usr/bin/env python3
"""生成科研绘图示例集合 sciviz_examples.json（来自 ~/Downloads/Code_Notebook）。

转换规则（ipynb → 单文件 .py）：
  1. 仅抽取 code cell，按顺序拼接；
  2. 剥离 magic（%开头）与 shell 残留（!开头 / open·pdfcrop 开头的 macOS 命令行）；
  3. 去重重复 import 行（notebook 各 cell 反复 import 同一库）；
  4. savefig 的 '../../figures/...' 库外路径改写为运行目录相对文件名，
     保证 sidecar 资源扫描可见；
  5. plt.show() → 编号 PNG 保存（运行环境无交互窗口，沿 gen_dataviz_examples 先例）；
  6. 注入中文字体配置（PingFang 等本机字体，找不到时降级不报错）；
  7. 第三方 import 自动并入 requirements 声明（read_excel 额外补 openpyxl）。

数据与模块资产：按代码引用扫描，把 notebook 所在章节的 data/Data 子目录整目录
拷入 examples_assets/code_notebook/<chapter>/，引用文件缺失时按文件名全库回源补拷
（Wang2020 等浏览器改名场景）；内嵌模块（ternary_new、nice.py）按 MODULE_ASSETS 拷贝。
JSON 的 dir 字段指向资产目录，物化时数据与兄弟模块自动就位。

跳过项：Python语法简介 / _backup / *_training 变体 / 下载数据.ipynb（与正文重复或无复用价值）。

用法：python scripts/gen_sciviz_examples.py
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_ROOT = Path.home() / "Downloads" / "Code_Notebook"
ASSETS = ROOT / "examples_assets" / "code_notebook"
OUT = ROOT / "json_examples" / "sciviz_examples.json"
DATA_EXT = (".csv", ".xlsx", ".nc", ".dat", ".txt", ".json")

FONT_HELPER = """# 中文字体配置（找不到中文字体时中文显示为方块但不影响运行）
try:
    from matplotlib import font_manager as _fm
    _zh = [f.name for f in _fm.fontManager.ttflist if any(
        k in f.name for k in ("PingFang", "Heiti", "Songti", "Hiragino", "YaHei", "SimHei", "Arial Unicode"))]
    if _zh:
        plt.rcParams["font.sans-serif"] = [_zh[0]]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass
"""

# 内嵌模块资产：notebook 相对路径 → 需随 dir 就位的模块/文件（相对章节目录）
MODULE_ASSETS: dict[str, list[str]] = {
    "Chapter2/Lecture2_8.ipynb": ["ternary_new"],
    "Chapter4/Chapter4_2.ipynb": ["nice.py"],
    "Chapter4/Chapter4_3.ipynb": ["nice.py"],
    "Chapter4/Chapter4_4.ipynb": ["nice.py"],
}

# (notebook 相对路径, 文件名, 标题, 描述, 标签)
ENTRIES = [
    # ---- 第一章：matplotlib 基础 ----
    ("Chapter1/画布及坐标轴.ipynb", "sciviz-canvas-axes.py", "画布与坐标轴（科研绘图）",
     "matplotlib 画布（figure）与坐标轴（axes）的创建、层级关系与常用参数，科研绘图的起点"
     "（Code Notebook 第一章）。",
     ["科研绘图", "坐标轴", "matplotlib"]),
    ("Chapter1/复杂坐标轴+多图创建.ipynb", "sciviz-complex-axes.py", "复杂坐标轴与多图布局（科研绘图）",
     "对数/对数-对数坐标系、双轴、Insets 局部放大与多子图布局（GridSpec），论文复杂版式的绘制方法"
     "（Code Notebook 第一章第三节）。",
     ["科研绘图", "对数坐标", "多子图"]),
    ("Chapter1/数据读取.ipynb", "sciviz-data-formats.py", "科学数据格式读取（科研绘图）",
     "netCDF4/h5py/meshio/文本等科学数据格式的读取与预览，演示 ETOPO 地形、非结构网格等真实数据"
     "（Code Notebook 第一章第四节）。",
     ["科研绘图", "数据读取", "netCDF4"]),
    # ---- 第二章：基础二维图 ----
    ("Chapter2/Lecture2_1.ipynb", "sciviz-pandas-plot.py", "pandas 论文数据绘图（科研绘图）",
     "pandas 读取 Nature 论文增补数据并绘制趋势图，复现 Bennett 2019 与 Heap 2019 的科研数据案例"
     "（Code Notebook Lecture 2.1）。",
     ["科研绘图", "pandas", "论文复现"]),
    ("Chapter2/Lecture2_2.ipynb", "sciviz-line-styles.py", "折线图全参数演示（科研绘图）",
     "演示 plot 的线宽、颜色、透明度、marker、虚线与 clip_on 全套线型参数，并含两个论文复现"
     "实战（Shackleton 2020 多子图拼版与 Wang 2020 Nature 增补数据），数据随 dir 目录就位"
     "（Code Notebook Lecture 2.2）。",
     ["科研绘图", "折线图", "论文复现"]),
    ("Chapter2/Lecture2_3.ipynb", "sciviz-slope-graph.py", "基础蛛网图（科研绘图）",
     "复现 Zhao 2019 论文图 2 的蛛网图（对角线交互图），演示论文级斜率对比图的绘制（Code Notebook Lecture 2.3）。",
     ["科研绘图", "蛛网图", "论文复现"]),
    ("Chapter2/Lecture2_4.ipynb", "sciviz-bar-basics.py", "柱状图基础（科研绘图）",
     "单组与多组数据的柱状对比，柱宽、颜色、边框与误差棒的基础参数（Code Notebook Lecture 2.4）。",
     ["科研绘图", "柱状图", "matplotlib"]),
    ("Chapter2/Lecture2_5.ipynb", "sciviz-grouped-bars.py", "并列与层叠柱状图（科研绘图）",
     "复现 Susanne Nature 2020 Figure3b 的分组构成对比，演示并列与层叠柱状图的论文画法"
     "（Code Notebook Lecture 2.5）。",
     ["科研绘图", "柱状图", "论文复现"]),
    ("Chapter2/Lecture2_6.ipynb", "sciviz-pie-donut.py", "饼图与环形图（科研绘图）",
     "以 VentFields 数据演示占比构成的可视化、百分比标签与环形图排版（Code Notebook Lecture 2.6）。",
     ["科研绘图", "饼图", "占比"]),
    ("Chapter2/Lecture2_7.ipynb", "sciviz-polar-rose.py", "玫瑰图与极坐标系（科研绘图）",
     "方位/风向数据的极坐标统计与玫瑰图美化，演示极坐标系的科研用法（Code Notebook Lecture 2.7）。",
     ["科研绘图", "极坐标", "玫瑰图"]),
    ("Chapter2/Lecture2_8.ipynb", "sciviz-ternary.py", "三角图（ternary plot，科研绘图）",
     "基于内嵌 ternary_new 库绘制三组分相图与轨迹线，地球化学/材料学常用图型（Code Notebook Lecture 2.8）。",
     ["科研绘图", "三角图", "ternary"]),
    ("Chapter2/Lecture2_9.ipynb", "sciviz-contour-fields.py", "二维物理场等值线图（科研绘图）",
     "netCDF/dat 物理场数据的 contour 等值线与 colorbar 定制，海洋模型数据可视化（Code Notebook Lecture 2.9）。",
     ["科研绘图", "等值线", "物理场"]),
    ("Chapter2/Lecture2_10.ipynb", "sciviz-pcolor-fields.py", "二维物理场色彩图（科研绘图）",
     "海洋模型数据的 pcolor/色彩图渲染与色标（cmap）定制（Code Notebook Lecture 2.10）。",
     ["科研绘图", "色彩图", "物理场"]),
    ("Chapter2/Lecture2_11.ipynb", "sciviz-streamplot.py", "二维流场图（科研绘图）",
     "全球风场 netCDF 数据的 streamplot 流线可视化，密度与线宽映射风速（Code Notebook Lecture 2.11）。",
     ["科研绘图", "流场图", "streamplot"]),
    # ---- 第三章：进阶可视化 ----
    ("Chapter3/Chapter3_2.ipynb", "sciviz-unstructured-mesh.py", "非结构化网格可视化（科研绘图）",
     "meshio/h5py 读取有限元非结构网格并渲染，演示网格数据的科学可视化（Code Notebook Lecture 3.2）。",
     ["科研绘图", "非结构网格", "meshio"]),
    ("Chapter3/Chapter3_3.ipynb", "sciviz-seaborn-stats.py", "seaborn 统计分布图（科研绘图）",
     "以 seaborn 在 matplotlib 之上绘制统计分布图，演示科研场景中 KDE 与 rug 的组合用法"
     "（Code Notebook Lecture 3.3）。",
     ["科研绘图", "seaborn", "统计分布"],
     False),
    ("Chapter3/Chapter3_4.ipynb", "sciviz-venn-diagram.py", "韦恩图（matplotlib_venn）",
     "用 matplotlib_venn 绘制二/三集合韦恩图并自定义区域颜色与标签，适合论文中的集合关系展示"
     "（Code Notebook Lecture 3.4）。",
     ["科研绘图", "韦恩图", "集合关系"],
     False),
    ("Chapter3/Chapter3_5.ipynb", "sciviz-dendrogram.py", "系统树状图（层次聚类，科研绘图）",
     "scipy hierarchy 层次聚类 + mtcars 数据的树状图可视化（Code Notebook Lecture 3.5）。",
     ["科研绘图", "树状图", "层次聚类"]),
    ("Chapter3/Chapter3_6.ipynb", "sciviz-chord-diagram.py", "和弦图（chord diagram，科研绘图）",
     "关系矩阵数据的和弦图绘制，展示实体间的流向与关联（Code Notebook Lecture 3.6）。",
     ["科研绘图", "和弦图", "关系数据"]),
    ("Chapter3/Chapter3_7.ipynb", "sciviz-box-violin.py", "箱形图与小提琴图（科研绘图）",
     "数据分布对比的两种统计图形：箱形图分位数标注与小提琴图密度形态（Code Notebook Lecture 3.7）。",
     ["科研绘图", "箱线图", "小提琴图"]),
    ("Chapter3/Chapter3_8.ipynb", "sciviz-wordcloud.py", "词云图（科研绘图）",
     "word_cloud 生成中英文词云，自定义形状、配色与停用词（Code Notebook Lecture 3.8）。",
     ["科研绘图", "词云", "wordcloud"]),
    # ---- 第四章：出版级 3D ----
    ("Chapter4/Chapter4_2.ipynb", "sciviz-3d-surface.py", "三维曲面图（科研绘图）",
     "出版级 nice 风格的 3D 曲面绘制，轴样式与视角控制（Code Notebook Lecture 4.2）。",
     ["科研绘图", "3D 绘图", "曲面"]),
    ("Chapter4/Chapter4_3.ipynb", "sciviz-3d-profile.py", "三维剖面图（科研绘图）",
     "3D 剖面与 niceAxis 轴美化组合，论文级剖面呈现（Code Notebook Lecture 4.3）。",
     ["科研绘图", "3D 绘图", "剖面"]),
    ("Chapter4/Chapter4_4.ipynb", "sciviz-3d-bars.py", "三维柱状图（科研绘图）",
     "出版级 3D 柱状图绘制与颜色映射（Code Notebook Lecture 4.4）。",
     ["科研绘图", "3D 绘图", "柱状图"]),
]

# ---- 自动发现：把 Code_Notebook 中尚未收录的笔记本全部转为示例 ----
_seen_rels = {e[0] for e in ENTRIES}
for _root in sorted(NB_ROOT.glob("Chapter*")):
    for _nb in sorted(_root.glob("*.ipynb")):
        _rel = _nb.relative_to(NB_ROOT).as_posix()
        if _rel in _seen_rels or ".ipynb_checkpoints" in _rel or "_backup" in _rel:
            continue
        _title = _nb.stem.replace("_", " ").strip() or _nb.stem
        ENTRIES.append((_rel, f"sciviz-auto-{_title}.py", f"{_title}（科研绘图）",
                        f"由 {_rel} 转换的科研绘图示例（自动收录）。", ["科研绘图", "matplotlib", "自动收录"]))


def notebook_code(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts: list[str] = []
    seen_imports: set[str] = set()
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        lines = "".join(cell.get("source", [])).splitlines()
        cleaned: list[str] = []
        for line in lines:
            s = line.strip()
            if s.startswith(("%", "!")) or re.match(r"^(open|pdfcrop)\s+\S+\.(pdf|png)", s):
                continue
            if "os.system" in s and "pdfcrop" in s:
                continue  # pdfcrop 是 TeX 工具链的装饰性后处理，非教学内容且运行环境无此工具
            m = re.match(r"^(?:import|from)\s+\S+", s)
            if m:
                if s in seen_imports:
                    continue
                seen_imports.add(s)
            cleaned.append(line)
        if cleaned:
            parts.append("\n".join(cleaned))
    return "\n\n".join(parts)


def post_process(code: str, stem: str) -> str:
    # savefig 的库外路径 → 运行目录文件名（含 ../../figures/ChapterN/ 前缀与 ../ 变体）
    code = re.sub(
        r"(['\"])(?:\.\./)+(?:figures/[\w\-]+/)?([^/'\"]+\.(?:pdf|png|eps|svg))\1",
        r"\1\2\1",
        code,
    )
    # plt.show() → 编号 PNG 保存（sidecar 扫描运行目录图片供前端预览）
    counter = {"n": 0}

    def _show(m: re.Match) -> str:
        counter["n"] += 1
        suffix = "" if counter["n"] == 1 else f"_{counter['n']}"
        return f"plt.savefig('{stem}_preview{suffix}.png', bbox_inches='tight', dpi=110)\nplt.close('all')"

    code = re.sub(r"plt\.show\(\)", _show, code)
    if "import matplotlib.pyplot as plt" in code and "font_manager as _fm" not in code:
        code = code.replace("import matplotlib.pyplot as plt", "import matplotlib.pyplot as plt\n" + FONT_HELPER, 1)
    return code


def copy_ref_file(chapter_dir: Path, ref: str, assets_chapter: Path) -> bool:
    """按引用相对路径拷贝单个数据文件；缺失时按文件名在章节目录下回源。"""
    src = chapter_dir / ref
    if not src.is_file():
        found = list(chapter_dir.rglob(Path(ref).name))
        if not found:
            return False
        src = found[0]
    dst = assets_chapter / ref
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def sync_assets(code: str, rel: str, assets_chapter: Path) -> bool:
    """扫描代码引用的数据文件并拷入资产目录；内嵌模块按 MODULE_ASSETS 拷贝。

    引用的数据集子目录（data/<名>/ 或 Data/<名>/）整目录拷贝，保证拼接路径也能命中；
    引用文件在源侧缺失时按文件名回源补拷（浏览器改名场景）。返回是否有资产就位。
    """
    chapter_dir = NB_ROOT / rel.split("/")[0]
    assets_chapter.mkdir(parents=True, exist_ok=True)
    refs = re.findall(r"['\"]([^'\"]+\.(?:csv|xlsx|nc|dat|txt|json))['\"]", code)
    copied = False
    data_dirs: set[str] = set()
    for ref in refs:
        if ref.startswith("/") or ".." in ref:
            continue
        parts = Path(ref).parts
        if len(parts) >= 2 and parts[0] in ("data", "Data"):
            data_dirs.add(f"{parts[0]}/{parts[1]}")
        if copy_ref_file(chapter_dir, ref, assets_chapter):
            copied = True
    for dd in sorted(data_dirs):
        src = chapter_dir / dd
        if src.is_dir():
            dst = assets_chapter / dd
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(
                src,
                dst,
                ignore=shutil.ignore_patterns("__pycache__", ".ipynb_checkpoints", "*.png", "*.jpg", "*.pdf", "*.eps", "*.svg"),
                dirs_exist_ok=True,
            )
            copied = True
    for name in MODULE_ASSETS.get(rel, []):
        src = chapter_dir / name
        dst = assets_chapter / name
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied = True
        elif src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(
                src,
                dst,
                ignore=shutil.ignore_patterns("__pycache__", ".ipynb_checkpoints", "*.png", "*.jpg", "*.pdf", "*.eps", "*.svg"),
            )
            copied = True
    return copied


def main() -> None:
    import sys

    stdlib = set(sys.stdlib_module_names)
    examples = []
    for rel, name, title, desc, tags, *extra in ENTRIES:
        src = NB_ROOT / rel
        code = post_process(notebook_code(src), name[:-3])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(code)  # 语法必须有效
        if "os.system" in code or re.search(r"^\s*!", code, re.M):
            print(f"⊘ {rel}: 含 shell 调用，跳过")
            continue
        # 第三方 import 并入 requirements 声明（notebook 标准头部常带未用 import，
        # 缺依赖判定按 import 走，声明完整才能进共享依赖清单）
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                mods.add(n.module.split(".")[0])
        # requirements 卫生：剔除随 dir 就位的本地模块（非 PyPI 包），
        # import 名映射到 PyPI 名（PIL→pillow）；mpl_toolkits 由 matplotlib 提供，跳过
        local_modules = {"nice", "ternary_new"}
        import_aliases = {"PIL": "pillow", "mpl_toolkits": None}
        resolved: set[str] = set()
        for m in mods:
            if m in stdlib or m in local_modules:
                continue
            alias = import_aliases.get(m, m)
            if alias:
                resolved.add(alias.lower())
        all_reqs = sorted(resolved)
        if "read_excel" in code and "openpyxl" not in all_reqs:
            all_reqs.append("openpyxl")  # pandas 读 xlsx 的运行时依赖，import 扫描感知不到
        chapter = rel.split("/")[0].lower()
        assets_chapter = ASSETS / chapter
        has_assets = sync_assets(code, rel, assets_chapter)
        entry = {
            "id": f"topics_data-analysis_sciviz-{name}",
            "name": name,
            "category": "topics",
            "tags": tags,
            "title": title,
            "description": desc,
            "requirements": all_reqs,
            "code": code,
        }
        if has_assets:
            entry["dir"] = f"examples_assets/code_notebook/{chapter}"
        examples.append(entry)
        print(f"✓ {rel} → {name}（{len(code.splitlines())} 行，依赖 {all_reqs}，dir={'有' if has_assets else '-'}）")

    out = {
        "name": "科研绘图示例",
        "description": "来自 Code Notebook 教材的科研出版级绘图示例（ipynb 转换）。",
        "examples": examples,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写出：{OUT}（{len(examples)} 条）")


if __name__ == "__main__":
    main()
