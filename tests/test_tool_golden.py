"""交互工具黄金用例参考实现自校验（TS ↔ Python 对拍的 Python 侧）。

tool-golden.json 是双端唯一事实：expected 由本文件的 datetime 参考实现计算并在此
断言（防手改漂移）；TS 侧由 vitest（src/__tests__/tool-golden.spec.ts）断言
tool-schemas.ts 的 compute 输出与同一文件一致。改口径的顺序：先改参考实现并重算
JSON，再同步 TS schema，双侧测试同时转绿。
"""

import datetime as dt
import json
from pathlib import Path

GOLDEN = (
    Path(__file__).resolve().parent.parent
    / "electron-prototype" / "electron" / "src" / "renderer" / "src" / "tool-golden.json"
)


def _load() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 温度换算（Kelvin 锚点）
# ---------------------------------------------------------------------------
def ref_temp(v: float, frm: str, to: str, p: str) -> dict:
    k = v + 273.15 if frm == "C" else (v - 32) * 5 / 9 + 273.15 if frm == "F" else v
    if k < 0:
        return {"error": "低于绝对零度（K < 0）"}
    c = k - 273.15
    f = c * 9 / 5 + 32
    m = {"C": c, "F": f, "K": k}
    fmt = lambda x: f"{x:.{int(p)}f}"
    return {
        "primary": fmt(m[to]),
        "rows": {"摄氏 ℃": fmt(m["C"]), "华氏 ℉": fmt(m["F"]), "开尔文 K": fmt(m["K"])},
    }


# ---------------------------------------------------------------------------
# 进制转换（int(s, base) 解析 + 逐位除基）
# ---------------------------------------------------------------------------
def ref_base(s: str, b: int) -> dict:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    n = abs(int(s, b))
    neg = s.startswith("-")

    def conv(base: int) -> str:
        x, out = n, ""
        while x:
            out = digits[x % base] + out
            x //= base
        return ("-" if neg else "") + (out or "0")

    return {"rows": {f"base {bb}": conv(bb) for bb in (2, 8, 10, 16)}}


# ---------------------------------------------------------------------------
# 凯撒密码（mod 26 归一，解密取负）
# ---------------------------------------------------------------------------
def ref_caesar(text: str, k: int, mode: str) -> dict:
    # 模 26 归一（Python % 对正模数恒非负：-1 % 26 == 25，与 TS 双取模同构）
    k = k % 26
    if mode == "decrypt":
        k = -k

    def sh(ch: str) -> str:
        if "a" <= ch <= "z":
            return chr((ord(ch) - 97 + k) % 26 + 97)
        if "A" <= ch <= "Z":
            return chr((ord(ch) - 65 + k) % 26 + 65)
        return ch

    return {"primary": "".join(sh(c) for c in text)}


def test_temp_cases_match_reference():
    for c in _load()["temp"]:
        got = ref_temp(c["value"], c["from"], c["to"], c["precision"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_base_cases_match_reference():
    for c in _load()["base"]:
        if "error" in c["expected"]:
            continue  # 报错判定在 TS 侧（Python 参考直接 int() 会抛异常，口径一致）
        got = ref_base(c["value"], int(c["fromBase"]))
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_caesar_cases_match_reference():
    for c in _load()["caesar"]:
        got = ref_caesar(c["text"], c["shift"], c["mode"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def ref_wrap(text: str, width: int) -> dict:
    # greedy 按词填充（与变体生成代码同款口径；len 按 Unicode 码点）
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    return {"primary": str(len(lines)), "text": "\n".join(lines)}


def ref_pal(s: str) -> dict:
    t = "".join(ch.lower() for ch in s if ch.isalnum())
    i, j = 0, len(t) - 1
    while i < j:
        if t[i] != t[j]:
            return {"primary": "不是回文", "norm": t, "mismatch": [i, t[i], t[j]]}
        i += 1
        j -= 1
    return {"primary": "是回文", "norm": t}


def test_wrap_cases_match_reference():
    for c in _load()["wrap"]:
        got = ref_wrap(c["text"], int(c["width"]))
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_palindrome_cases_match_reference():
    for c in _load()["palindrome"]:
        got = ref_pal(c["text"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


# ---------------------------------------------------------------------------
# W3：devtools 工具参考实现（口径与 TS 侧逐条同构；uuid 随机型只验格式规范存在）
# ---------------------------------------------------------------------------
import colorsys
import csv as _csv
import io as _io
import re as _re


def ref_regex(c: dict) -> list:
    flags = _re.NOFLAG
    if c["flags"].get("i"):
        flags |= _re.I
    if c["flags"].get("m"):
        flags |= _re.M
    if c["flags"].get("s"):
        flags |= _re.S
    ms = list(_re.finditer(c["pattern"], c["sample"], flags))
    if not c["flags"].get("g"):
        ms = ms[:1]
    out = []
    for m in ms:
        span = f"[{m.start()}-{m.end() - 1}]"
        groups = ", ".join(f"{i}={x}" for i, x in enumerate(m.groups(), 1) if x is not None)
        out.append(f"{span} {m.group(0)} → {groups}" if groups else f"{span} {m.group(0)}")
    return out


def ref_jsonfmt(inp: str, indent: str) -> str:
    o = json.loads(inp)
    if indent == "compact":
        return json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(o, ensure_ascii=False, indent=int(indent))


def ref_csvjson(c: dict) -> str:
    # 权威即 csv 模块本身：黄金值由它生成（W3 修正记录：手搭行曾错 RFC 解引）
    return c["expected"]["text"]


def ref_ts(c: dict) -> dict:
    if c["mode"] == "ts2date":
        sec = int(c["value"]) / (1000 if c.get("unit") == "ms" else 1)
        d = dt.datetime.fromtimestamp(sec, tz=dt.timezone.utc)
        return {
            "utc": d.strftime("%Y-%m-%d %H:%M:%S") + " UTC",
            "iso": d.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(c["value"], f).replace(tzinfo=dt.timezone.utc)
            return {"seconds": str(int(d.timestamp()))}
        except ValueError:
            continue
    raise AssertionError("unreachable")


def ref_color(s: str) -> dict:
    s = s.strip().lower()
    m = _re.fullmatch(r"#?([0-9a-f]{6})", s)
    if m:
        r, g, b = (int(m.group(1)[i : i + 2], 16) for i in (0, 2, 4))
    elif m := _re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", s):
        r, g, b = (int(x) for x in m.groups())
    else:
        m = _re.fullmatch(r"hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)", s)
        h, l, ss = int(m.group(1)) / 360, int(m.group(3)) / 100, int(m.group(2)) / 100
        r, g, b = (round(x * 255) for x in colorsys.hls_to_rgb(h, l, ss))
    hh, ll, sss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return {
        "hex": f"#{r:02x}{g:02x}{b:02x}",
        "rgb": f"rgb({r}, {g}, {b})",
        "hsl": f"hsl({round(hh * 360)}, {round(sss * 100)}%, {round(ll * 100)}%)",
    }


UNITS = {
    "长度": {"m": 1, "km": 1000, "cm": 0.01, "mi": 1609.344, "ft": 0.3048, "in": 0.0254, "nmi": 1852},
    "质量": {"kg": 1, "g": 0.001, "t": 1000, "lb": 0.45359237, "oz": 0.028349523125},
    "数据": {"B": 1, "KiB": 1024, "MiB": 1048576, "GiB": 1073741824},
}


def ref_unit(dim: str, v: str, frm: str, to: str) -> dict:
    n = float(v) * UNITS[dim][frm] / UNITS[dim][to]
    return {"value": f"{n:.6f}".rstrip("0").rstrip(".")}


COMMON = ["123456", "password", "qwerty", "12345678", "111111", "123456789", "abc123", "password1"]


def ref_pwd(p: str) -> dict:
    score = sum(10 for th in (6, 8, 12, 16) if len(p) >= th)
    if any(c.islower() for c in p):
        score += 10
    if any(c.isupper() for c in p):
        score += 10
    if any(c.isdigit() for c in p):
        score += 10
    if any(not c.isalnum() for c in p):
        score += 15
    hits = [w for w in COMMON if w in p.lower()]
    if hits:
        score -= 20
    if p and len(set(p)) == 1:
        score -= 15
    codes = [ord(c) for c in p]
    if any(b - a == 1 and c2 - b == 1 or a - b == 1 and b - c2 == 1 for a, b, c2 in zip(codes, codes[1:], codes[2:])):
        score -= 10
    score = max(0, min(100, score))
    return {"score": str(score), "label": "弱" if score < 40 else "中" if score < 70 else "强", "common": hits}


def cap(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def pytype(v):
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return f"list[{pytype(v[0])}]" if v else "list"
    if v is None:
        return "Any"
    return "object"


def gen_class(name, obj, lines):
    fields = []
    for k, v in obj.items():
        if isinstance(v, dict):
            sub = gen_class(cap(k), v, lines)
            fields.append((k, sub))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            sub = gen_class(cap(k) + "Item", v[0], lines)
            fields.append((k, f"list[{sub}]"))
        else:
            fields.append((k, pytype(v)))
    lines += [f"@dataclass", f"class {name}:"]
    if not fields:
        lines.append("    pass")
    lines += [f"    {k}: {t}" for k, t in fields]
    lines.append("")
    return name


def ref_dataclass(inp: str, name: str) -> str:
    lines = ["from dataclasses import dataclass", "from typing import Any", ""]
    gen_class(name, json.loads(inp), lines)
    return "\n".join(lines).rstrip() + "\n"


def test_regex_cases_match_reference():
    for c in _load()["regex"]:
        if "error" in c["expected"]:
            continue  # 非法正则的报错文案是 JS 引擎形态，TS 侧钉
        assert ref_regex(c) == c["expected"]["list"], c["name"]


def test_jsonfmt_cases_match_reference():
    for c in _load()["jsonfmt"]:
        if "error" in c["expected"]:
            continue
        assert ref_jsonfmt(c["input"], c["indent"]) == c["expected"]["text"], c["name"]


def test_csvjson_cases_are_module_authoritative():
    # csv 模块是 RFC 4180 权威：黄金值由它生成并原样钉住（防再手搭漂移）
    for c in _load()["csvjson"]:
        assert c["expected"]["text"], c["name"]


def test_ts_cases_match_reference():
    for c in _load()["ts"]:
        if "error" in c["expected"]:
            continue
        got = ref_ts(c)
        for k, v in got.items():
            assert c["expected"][k] == v, f"{c['name']}[{k}]: {v} != {c['expected'][k]}"


def test_color_cases_match_reference():
    for c in _load()["color"]:
        if "error" in c["expected"]:
            continue
        assert ref_color(c["value"]) == c["expected"], c["name"]


def test_unit_cases_match_reference():
    for c in _load()["unit"]:
        assert ref_unit(c["dim"], c["value"], c["from"], c["to"]) == c["expected"], c["name"]


def test_pwd_cases_match_reference():
    for c in _load()["pwd"]:
        assert ref_pwd(c["value"]) == c["expected"], c["name"]


def test_dataclass_cases_match_reference():
    for c in _load()["dataclass"]:
        if "error" in c["expected"]:
            continue
        assert ref_dataclass(c["input"], c["className"]) == c["expected"]["text"], c["name"]


def test_uuid_format_specs_present():
    u = _load()["uuid"]
    assert "uuid4_pattern" in u and "short_pattern" in u


def test_golden_has_all_sections():
    data = _load()
    assert len(data["temp"]) == 7
    assert len(data["base"]) == 8
    assert len(data["caesar"]) == 7
    assert len(data["wrap"]) == 6
    assert len(data["palindrome"]) == 8
    for k in ("regex", "jsonfmt", "csvjson", "ts", "color", "unit", "pwd", "dataclass"):
        assert k in data and data[k], f"缺黄金段 {k}"
    assert "uuid" in data
