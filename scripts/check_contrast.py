#!/usr/bin/env python3
"""A1 视觉基线对比度门禁：从产品 token 源重算 WCAG 2.1 比率。

单一真值 = electron-prototype/electron/src/renderer/src/theme.css 的令牌块
（A2 起 token 已落产品；页稿 docs/a1-visual-baseline.html 冻结为评审存档）。
token 值一改，本脚本与基线文档 §4 的矩阵必须同步——避免"文档数字漂亮、
实现悄悄漂移"，也避免手抄矩阵出错。

口径（与 docs/redesign-visual-baseline.md §4 一致）：
- 材质面按声明的回退实色（--bg-sidebar-fallback）评估：桌面透出内容不可控，
  不能作为验收基准；win 深色半透明卡片先按 alpha 合成到窗口底色；
- 信息性文字阈值 4.5:1（WCAG 1.4.3）；
- 装饰/禁用（圆点、禁用文字、行号）记录口径 2.5:1；
- 强调填充上的文字按组件级 3.0:1 评估，未达文字 AA 的条目在文档偏差表记录。

用法：python3 scripts/check_contrast.py    （存在 FAIL 时退出码 1）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "electron-prototype" / "electron" / "src" / "renderer" / "src" / "theme.css"

COMBOS = [
    ("macOS 深色", ["html {"]),
    ("macOS 浅色", ["html {", 'html[data-theme="light"] {']),
    ("Windows 深色", ["html {", 'html[data-platform="win"] {']),
    (
        "Windows 浅色",
        [
            "html {",
            'html[data-theme="light"] {',
            'html[data-platform="win"] {',
            'html[data-platform="win"][data-theme="light"] {',
        ],
    ),
]


def parse_combo(text: str, markers: list[str]) -> dict[str, str]:
    """按 CSS 级联顺序合并变量块（后块覆盖前块，未重定义的沿用）。"""
    tokens: dict[str, str] = {}
    for marker in markers:
        start = text.index(marker)
        block = text[start : text.index("\n}", start)]
        tokens.update(
            {k: v.strip() for k, v in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block)}
        )
    return tokens


def to_rgb(value: str) -> tuple[float, float, float, float]:
    value = value.strip()
    if value.startswith("#"):
        h = value.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = re.fullmatch(r"rgba?\(([^)]+)\)", value)
    if not m:
        raise ValueError(f"无法解析颜色: {value}")
    parts = [p.strip() for p in m.group(1).split(",")]
    r, g, b = (float(p) for p in parts[:3])
    a = float(parts[3]) if len(parts) > 3 else 1.0
    return (r, g, b, a)


def over(
    fg: tuple[float, float, float, float], bg: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    """半透明 fg 叠在不透明 bg 上的合成色。"""
    a = fg[3]
    return (
        fg[0] * a + bg[0] * (1 - a),
        fg[1] * a + bg[1] * (1 - a),
        fg[2] * a + bg[2] * (1 - a),
        1.0,
    )


def luminance(rgb: tuple[float, float, float, float]) -> float:
    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b, _ = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(
    fg: tuple[float, float, float, float], bg: tuple[float, float, float, float]
) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def checks(t: dict[str, str]) -> list[tuple[str, str, str, float, float, str]]:
    """返回 (类别, 前景, 背景, 比值, 阈值, 判定)。"""
    window = to_rgb(t["bg-window"])
    chrome = to_rgb(t["bg-chrome"])
    sidebar = to_rgb(t["bg-sidebar-fallback"])
    card = over(to_rgb(t["bg-card"]), window)
    console = to_rgb(t["bg-console"])
    surfaces = {"window": window, "chrome": chrome, "sidebar": sidebar, "card": card}
    rows: list[tuple[str, str, str, float, float, str]] = []

    def add(cat: str, fg: str, bg: str, fg_rgb, bg_rgb, threshold: float) -> None:
        r = round(ratio(fg_rgb, bg_rgb), 2)
        rows.append((cat, fg, bg, r, threshold, "PASS" if r >= threshold else "FAIL"))

    for name, threshold, cat in (
        ("primary", 4.5, "text"),
        ("secondary", 4.5, "text"),
        ("tertiary", 4.5, "text"),
        ("quaternary", 2.5, "decoration"),
    ):
        fg_rgb = to_rgb(t[f"text-{name}"])
        for surf, bg_rgb in surfaces.items():
            add(f"{cat}.{name}", t[f"text-{name}"], surf, fg_rgb, bg_rgb, threshold)

    add(
        "console.text",
        t["text-console"],
        "console",
        to_rgb(t["text-console"]),
        console,
        4.5,
    )
    add(
        "console.gutter",
        t["text-gutter"],
        "console",
        to_rgb(t["text-gutter"]),
        console,
        2.5,
    )
    for part in ("kw", "str", "num", "cmt", "fn"):
        add(
            f"code.{part}",
            t[f"code-{part}"],
            "console",
            to_rgb(t[f"code-{part}"]),
            console,
            4.5,
        )

    for family in ("system", "brand"):
        add(
            f"accent.{family}.label",
            t[f"on-accent-{family}"],
            t[f"accent-{family}"],
            to_rgb(t[f"on-accent-{family}"]),
            to_rgb(t[f"accent-{family}"]),
            3.0,
        )
        for surf in ("window", "card"):
            add(
                f"accent.{family}.text",
                t[f"accent-{family}-text"],
                surf,
                to_rgb(t[f"accent-{family}-text"]),
                surfaces[surf],
                4.5,
            )

    for status in ("green", "red", "amber"):
        for surf in ("window", "card"):
            add(
                f"status.{status}",
                t[f"status-{status}"],
                surf,
                to_rgb(t[f"status-{status}"]),
                surfaces[surf],
                4.5,
            )

    info_bg = t.get("status-info-bg", "transparent")
    if not info_bg.startswith("transparent"):
        add(
            "status.amber-on-info",
            t["status-amber"],
            "status-info-bg",
            to_rgb(t["status-amber"]),
            to_rgb(info_bg),
            4.5,
        )
    return rows


def main() -> int:
    text = TOKENS.read_text(encoding="utf-8")
    failures = 0
    print(f"[contrast] 源: {TOKENS.relative_to(ROOT)}")
    for label, marker in COMBOS:
        tokens = parse_combo(text, marker)
        rows = checks(tokens)
        failed = [r for r in rows if r[5] == "FAIL"]
        failures += len(failed)
        print(f"\n### {label}（{len(rows)} 项，{len(failed)} 项失败）")
        for cat, fg, bg, r, threshold, verdict in rows:
            mark = "" if verdict == "PASS" else "  <<< FAIL"
            print(f"  {cat:<22} {fg:<22} on {bg:<16} {r:>6.2f}  (>= {threshold}){mark}")
    print(f"\n[contrast] {'全部通过' if not failures else f'{failures} 项失败'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
