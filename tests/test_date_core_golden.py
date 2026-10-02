"""date-core 黄金用例参考实现自校验（TS ↔ Python 对拍的 Python 侧）。

date-core.golden.json 是双端唯一事实：expected 由本文件的 datetime 参考实现
计算并在此断言（防手改漂移）；TS 侧由 vitest（components/__tests__/date-core.spec.ts）
断言 date-core.ts 输出与同一文件一致。改口径的顺序：先改参考实现并重算 JSON，
再同步 TS 实现，双侧测试同时转绿。
"""

import calendar as _cal
import json
import math
from datetime import date, timedelta
from pathlib import Path

GOLDEN = (
    Path(__file__).resolve().parent.parent
    / "electron-prototype" / "electron" / "src" / "renderer" / "src" / "date-core.golden.json"
)
WD = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def _p(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def _add_months(d: date, k: int) -> date:
    total = d.year * 12 + (d.month - 1) + k
    # divmod 对负 total 也做向下取整（floor），与 TS 侧 Math.floor(total / 12) 语义一致
    y, m0 = divmod(total, 12)
    return date(y, m0 + 1, min(d.day, _cal.monthrange(y, m0 + 1)[1]))


def _add_years(d: date, k: int) -> date:
    y = d.year + k
    return date(y, d.month, min(d.day, _cal.monthrange(y, d.month)[1]))


def ref_diff(a: date, b: date) -> dict:
    if b < a:
        a, b = b, a
    days = (b - a).days
    m = (b.year - a.year) * 12 + (b.month - a.month)
    if b.day < a.day:
        m -= 1
    rem = (b - _add_months(a, m)).days
    leap = sum(
        1
        for y in range(a.year, b.year + 1)
        if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) and date(y, 2, 29) >= a and date(y, 2, 29) < b
    )
    return {
        "days": days,
        "weeks": f"{days / 7:.1f}",
        "norm": [m // 12, m % 12, rem],
        "leap_days": leap,
        "weekday_a": WD[a.weekday()],
        "weekday_b": WD[b.weekday()],
    }


def ref_add(s: str, n: int, unit: str) -> str:
    d = _p(s)
    if unit == "day":
        r = d + timedelta(days=n)
    elif unit == "week":
        r = d + timedelta(days=7 * n)
    elif unit == "month":
        r = _add_months(d, n)
    else:
        r = _add_years(d, n)
    return r.isoformat()


def ref_anniv(s: str, today: str, count: int = 3) -> list:
    d, t = _p(s), _p(today)
    cands = []
    # (t - d) < 0 时 ceil 可能算出 0 甚至负数，max(1, ·) 兜底保证从满 100 天起步
    k0 = max(1, math.ceil((t - d).days / 100))
    cands += [(d + timedelta(days=100 * k), f"满 {100 * k} 天") for k in range(k0, k0 + 8)]
    y0 = max(1, t.year - d.year - 1)
    got = 0
    for k in range(y0, y0 + 20):
        if got >= 8:
            break
        a = _add_years(d, k)
        if a >= t:
            cands.append((a, f"{k} 周年"))
            got += 1
    # tie-break：同日非周年在前（False < True），等价 TS 侧 yearly 标志；两侧标签都是自产的，等价成立
    cands.sort(key=lambda pair: (pair[0], "周" in pair[1]))
    out, used = [], set()
    for dt, label in cands:
        if dt in used:
            continue
        used.add(dt)
        out.append([dt.isoformat(), label])
        if len(out) == count:
            break
    return out


def _load() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_diff_cases_match_reference():
    for c in _load()["diff_cases"]:
        got = ref_diff(_p(c["a"]), _p(c["b"]))
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_add_cases_match_reference():
    for c in _load()["add_cases"]:
        got = ref_add(c["date"], c["n"], c["unit"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_anniversary_cases_match_reference():
    for c in _load()["anniversary_cases"]:
        got = ref_anniv(c["date"], c["today"], c["count"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_golden_has_all_sections():
    data = _load()
    # 精确计数：删用例要在结构上红，防止静默缩水
    assert len(data["diff_cases"]) == 8
    assert len(data["add_cases"]) == 6
    assert len(data["anniversary_cases"]) == 3
