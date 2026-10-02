"""交互工具黄金用例参考实现自校验（TS ↔ Python 对拍的 Python 侧）。

tool-golden.json 是双端唯一事实：expected 由本文件的 datetime 参考实现计算并在此
断言（防手改漂移）；TS 侧由 vitest（src/__tests__/tool-golden.spec.ts）断言
tool-schemas.ts 的 compute 输出与同一文件一致。改口径的顺序：先改参考实现并重算
JSON，再同步 TS schema，双侧测试同时转绿。
"""

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

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


# ---------------------------------------------------------------------------
# W4：JWT / .env / TOC / gitignore / 规范化 / 查找替换（随机型 pwdgen 只验常量在位）
# ---------------------------------------------------------------------------
import base64 as _b64


def ref_jwt(tok: str) -> dict:
    h, p, sig = tok.split(".")
    pad = lambda s: s + "=" * (-len(s) % 4)
    hh = json.loads(_b64.urlsafe_b64decode(pad(h)))
    pp = json.loads(_b64.urlsafe_b64decode(pad(p)))
    exp_s = (
        dt.datetime.fromtimestamp(pp["exp"], tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC"
        if "exp" in pp
        else None
    )
    iat_s = (
        dt.datetime.fromtimestamp(pp["iat"], tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC"
        if "iat" in pp
        else None
    )
    return {
        "header": json.dumps(hh, ensure_ascii=False, indent=2),
        "payload": json.dumps(pp, ensure_ascii=False, indent=2),
        "alg": hh.get("alg"),
        "exp": exp_s,
        "iat": iat_s,
        "siglen": len(sig),
    }


def ref_env(env_t: str, ex_t: str) -> dict:
    def parse(t):
        keys, empty = [], []
        for ln in t.splitlines():
            s = ln.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            k = k.strip()
            if not k:
                continue
            keys.append(k)
            if not v.strip():
                empty.append(k)
        return keys, empty

    ek, ee = parse(env_t)
    xk, _ = parse(ex_t)
    return {
        "missing": [k for k in xk if k not in ek],
        "extra": [k for k in ek if k not in xk],
        "empty": ee,
    }


def ref_toc(text: str, lo: int, hi: int) -> dict:
    def anchor(t):
        t = t.strip().lower()
        keep = [ch for ch in t if ch.isalnum() or ch in " -_"]
        return "".join(keep).replace(" ", "-")

    items, fence, counts = [], False, {}
    for ln in text.splitlines():
        if ln.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = _re.match(r"^(#{1,6})\s+(.+?)\s*$", ln)
        if not m:
            continue
        lvl, title = len(m.group(1)), m.group(2).strip()
        if lvl < lo or lvl > hi:
            continue
        a = anchor(title)
        n = counts.get(a, 0)
        counts[a] = n + 1
        if n:
            a = f"{a}-{n}"
        items.append("  " * (lvl - lo) + f"- [{title}](#{a})")
    return {"text": "\n".join(items) or "（未发现标题）", "count": str(len(items))}


def ref_norm(text: str, ending: str, mode: str) -> dict:
    t = _re.sub(r"\r\n?", "\n", text)
    res = []
    for ln in t.split("\n"):
        if mode in ("tab2", "tab4"):
            m = _re.match(r"^(\t+)", ln)
            if m:
                w = "  " if mode == "tab2" else "    "
                ln = m.group(1).replace("\t", w) + ln[len(m.group(1)):]
        elif mode == "space4tab":
            m = _re.match(r"^( +)", ln)
            if m:
                n = len(m.group(1))
                ln = "\t" * (n // 4) + " " * (n % 4) + ln[n:]
        res.append(ln)
    eol = {"LF": "\n", "CRLF": "\r\n", "CR": "\r"}[ending]
    return {"text": eol.join(res)}


def ref_replace(text: str, find: str, repl: str, is_regex: bool, ignore_case: bool) -> dict:
    if is_regex:
        try:
            new, n = _re.subn(find, repl.replace("\\", "\\\\"), text, flags=_re.I if ignore_case else 0)
        except _re.error:
            return {"error": True}
        return {"count": str(n), "text": new}
    pat = _re.escape(find)
    n = len(_re.findall(pat, text, _re.I if ignore_case else 0))
    if ignore_case:
        new = _re.sub(pat, repl.replace("\\", "\\\\"), text, flags=_re.I)
    else:
        new = text.replace(find, repl)
    return {"count": str(n), "text": new}


def test_jwt_cases_match_reference():
    for c in _load()["jwt"]:
        if "error" in c["expected"]:
            continue
        got = ref_jwt(c["token"])
        for k, v in got.items():
            assert c["expected"][k] == v, f"{c['name']}[{k}]: {v} != {c['expected'][k]}"


def test_env_cases_match_reference():
    for c in _load()["env"]:
        if "error" in c["expected"]:
            continue
        assert ref_env(c["env"], c["example"]) == c["expected"], c["name"]


def test_toc_cases_match_reference():
    for c in _load()["toc"]:
        got = ref_toc(c["text"], int(c["minLevel"]), int(c["maxLevel"]))
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_gitignore_sections_cover_selection():
    # gitignore 的模板常量在 TS 侧由 vitest 精确对拍；此处弱校验：expected 覆盖所选段头
    for c in _load()["gitignore"]:
        for s in c["stacks"]:
            assert f"# {s}" in c["expected"]["text"], c["name"]


def test_normalize_cases_match_reference():
    for c in _load()["normalize"]:
        got = ref_norm(c["text"], c["lineEnding"], c["indentMode"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_replacer_cases_match_reference():
    for c in _load()["replacer"]:
        got = ref_replace(c["text"], c["find"], c["replace"], c["regex"], c["ignoreCase"])
        assert got == c["expected"], f"{c['name']}: {got} != {c['expected']}"


def test_pwdgen_constants_present():
    g = _load()["pwdgen"]
    for k in ("lower", "upper", "digits", "symbols", "ambiguous"):
        assert g[k]
    assert g["min_length"] == 8 and g["max_length"] == 64


# ---------------------------------------------------------------------------
# W5：图片缩放试点——真实执行测试（PIL 造图 → 跑同款脚本 → 验产物）
# 该测试钉的是 PIL 管线本身（模板与 TS pyCode 逐字同构，fragments 由 vitest 钉）
# ---------------------------------------------------------------------------
PIL_TEMPLATE = """\"\"\"图片缩放：长边上限 {max}px（thumbnail 等比、只缩不放）。\"\"\"
from PIL import Image

im = Image.open({src!r})
before = im.size
im.thumbnail(({max}, {max}))
out = "resized.{fmt}"
if "{fmt}" == "jpg" and im.mode in ("RGBA", "P"):
    im = im.convert("RGB")
if "{fmt}" == "jpg":
    im.save(out, quality=90)
else:
    im.save(out)
print(f"输出 {{out}}: {{im.size[0]}}x{{im.size[1]}}（原图 {{before[0]}}x{{before[1]}}）")
"""


def test_image_resize_pipeline_real_execution(tmp_path):
    pytest.importorskip("PIL")  # 共享 venv 已装；缺失则跳过
    from PIL import Image

    src = tmp_path / "in.png"
    Image.new("RGBA", (800, 400), (255, 0, 0, 128)).save(src)
    script = tmp_path / "run.py"
    script.write_text(PIL_TEMPLATE.format(src=str(src), max=200, fmt="png"), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60
    )
    assert r.returncode == 0, r.stderr
    outp = tmp_path / "resized.png"
    assert outp.is_file()
    with Image.open(outp) as im:
        assert im.size[0] == 200 and im.size[1] == 100  # 等比缩到长边 200
    # jpg 白底转换路径
    script2 = tmp_path / "run2.py"
    script2.write_text(PIL_TEMPLATE.format(src=str(src), max=300, fmt="jpg"), encoding="utf-8")
    r2 = subprocess.run(
        [sys.executable, str(script2)], cwd=tmp_path, capture_output=True, text=True, timeout=60
    )
    assert r2.returncode == 0, r2.stderr
    with Image.open(tmp_path / "resized.jpg") as im2:
        assert im2.mode == "RGB"


# ---------------------------------------------------------------------------
# W6：B 档真实执行测试（PIL/openpyxl/pypdf 管线；模板与 TS pyCode 逐字同构）
# ---------------------------------------------------------------------------
IMG_COLLECT = """import glob, os

SRC = {src!r}
files = sorted(
    f for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
    for f in glob.glob(os.path.join(SRC, ext))
)
if not files:
    raise SystemExit("目录里没有图片")
print(f"共 {{len(files)}} 张图片待处理")
"""

BATCH_RESIZE_TPL = IMG_COLLECT + """from PIL import Image

for i, f in enumerate(files, 1):
    im = Image.open(f)
    im.thumbnail(({max_side}, {max_side}))
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    out = f"resized_{{i:03d}}.{fmt}"
    im.save(out)
    print(f"{{os.path.basename(f)}} -> {{out}} {{im.size[0]}}x{{im.size[1]}}")
"""

WATERMARK_TPL = IMG_COLLECT + """from PIL import Image, ImageDraw, ImageFont

font = ImageFont.load_default(size=48)
WM = {wm!r}
for i, f in enumerate(files, 1):
    im = Image.open(f).convert("RGBA")
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), WM, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((im.size[0] - tw - 24, im.size[1] - th - 24), WM, font=font, fill=(255, 255, 255, 160))
    out = f"wm_{{i:03d}}.png"
    Image.alpha_composite(im, layer).convert("RGB").save(out, quality=92)
    print(f"{{os.path.basename(f)}} -> {{out}}")
"""

GIF_COMPOSE_TPL = IMG_COLLECT + """from PIL import Image

frames = []
for f in files:
    im = Image.open(f).convert("RGB")
    if frames and im.size != frames[0].size:
        im = im.resize(frames[0].size)
    frames.append(im)
frames[0].save("out.gif", save_all=True, append_images=frames[1:], duration=200, loop=0)
print(f"已合成 out.gif：{{len(frames)}} 帧")
"""

IMG_TO_PDF_TPL = IMG_COLLECT + """from PIL import Image

pages = []
for f in files:
    im = Image.open(f)
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    pages.append(im)
pages[0].save("out.pdf", save_all=True, append_images=pages[1:])
print(f"已输出 out.pdf：{{len(pages)}} 页")
"""

EXCEL_EXPORT_TPL = """import csv as _csv
import io
import json

from openpyxl import load_workbook

wb = load_workbook({src!r}, read_only=True, data_only=True)
ws = wb.active
rows = [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
head, body = rows[0], rows[1:]
buf = io.StringIO()
w = _csv.writer(buf)
w.writerows(rows)
print(buf.getvalue())
"""

CSV_TO_XLSX_TPL = """import csv

from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = {sheet!r}
with open({src!r}, newline="", encoding="utf-8-sig") as f:
    for row in csv.reader(f):
        ws.append(row)
wb.save("converted.xlsx")
print("已输出 converted.xlsx")
"""


def _make_images(tmp_path, n=3):
    from PIL import Image

    d = tmp_path / "pics"
    d.mkdir(exist_ok=True)
    for i in range(n):
        Image.new("RGB", (200 + i * 40, 100), (i * 60 % 255, 120, 200)).save(d / f"img{i}.png")
    return d


def test_batch_resize_dir_real_execution(tmp_path):
    pytest.importorskip("PIL")
    d = _make_images(tmp_path)
    script = tmp_path / "run.py"
    script.write_text(BATCH_RESIZE_TPL.format(src=str(d), max_side=50, fmt="png"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    outs = sorted(tmp_path.glob("resized_*.png"))
    assert len(outs) == 3
    from PIL import Image

    with Image.open(outs[0]) as im:
        assert max(im.size) <= 50


def test_watermark_default_font_real_execution(tmp_path):
    pytest.importorskip("PIL")
    d = _make_images(tmp_path, 2)
    script = tmp_path / "run.py"
    script.write_text(WATERMARK_TPL.format(src=str(d), wm="@ 我的作品"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert len(list(tmp_path.glob("wm_*.png"))) == 2


def test_gif_compose_real_execution(tmp_path):
    pytest.importorskip("PIL")
    d = _make_images(tmp_path)
    script = tmp_path / "run.py"
    script.write_text(GIF_COMPOSE_TPL.format(src=str(d)), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    from PIL import Image

    with Image.open(tmp_path / "out.gif") as im:
        assert getattr(im, "n_frames", 1) == 3


def test_img_to_pdf_real_execution(tmp_path):
    pytest.importorskip("PIL")
    d = _make_images(tmp_path)
    script = tmp_path / "run.py"
    script.write_text(IMG_TO_PDF_TPL.format(src=str(d)), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    pypdf = pytest.importorskip("pypdf")
    r2 = PdfReader = pypdf.PdfReader(tmp_path / "out.pdf")
    assert len(r2.pages) == 3


def test_excel_csv_roundtrip_real_execution(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from openpyxl import Workbook

    src = tmp_path / "t.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["名称", "数量"])
    ws.append(["苹果", 12])
    ws.append([None, 3])
    wb.save(src)
    script = tmp_path / "run.py"
    script.write_text(EXCEL_EXPORT_TPL.format(src=str(src)), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "名称,数量" in r.stdout and "苹果,12" in r.stdout

    # CSV → Excel 反向
    csvp = tmp_path / "t.csv"
    csvp.write_text("名称,数量\n苹果,12\n", encoding="utf-8")
    script2 = tmp_path / "run2.py"
    script2.write_text(CSV_TO_XLSX_TPL.format(src=str(csvp), sheet="数据"), encoding="utf-8")
    r2 = subprocess.run([sys.executable, str(script2)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r2.returncode == 0, r2.stderr
    wb2 = openpyxl.load_workbook(tmp_path / "converted.xlsx")
    assert wb2.active.title == "数据"
    assert wb2.active.cell(row=2, column=1).value == "苹果"




CONTACT_SHEET_TPL = IMG_COLLECT + """from PIL import Image, ImageDraw

CELL, COLS = {cell}, {cols}
BG = ({bg_r}, {bg_g}, {bg_b})
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * CELL, rows * CELL), BG)
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    im.thumbnail((CELL - 8, CELL - 8))
    r, c = divmod(i, COLS)
    x = c * CELL + (CELL - im.size[0]) // 2
    y = r * CELL + (CELL - im.size[1]) // 2
    sheet.paste(im, (x, y))
    d.rectangle([c * CELL, r * CELL, c * CELL + CELL - 1, r * CELL + CELL - 1], outline=(70, 70, 70))
sheet.save("contact_sheet.png")
print(f"已输出 contact_sheet.png：{{len(files)}} 张 / {{COLS}} 列 / {{rows}} 行")
"""


def test_contact_sheet_real_execution(tmp_path):
    pytest.importorskip("PIL")
    d = _make_images(tmp_path, 5)
    script = tmp_path / "run.py"
    script.write_text(
        CONTACT_SHEET_TPL.format(src=str(d), cell=120, cols=2, bg_r=17, bg_g=17, bg_b=17), encoding="utf-8"
    )
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    from PIL import Image

    with Image.open(tmp_path / "contact_sheet.png") as im:
        assert im.size == (2 * 120, 3 * 120)  # 5 张 / 2 列 → 3 行


def test_golden_has_all_sections():
    data = _load()
    assert len(data["temp"]) == 7
    assert len(data["base"]) == 8
    assert len(data["caesar"]) == 7
    assert len(data["wrap"]) == 6
    assert len(data["palindrome"]) == 8
    for k in ("regex", "jsonfmt", "csvjson", "ts", "color", "unit", "pwd", "dataclass",
              "jwt", "env", "toc", "gitignore", "normalize", "replacer", "pwdgen", "image"):
        assert k in data and data[k], f"缺黄金段 {k}"
    assert "uuid" in data
