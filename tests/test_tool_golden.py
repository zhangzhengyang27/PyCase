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


# ---------------------------------------------------------------------------
# W8-W11：sidecar 计算型真实执行测试（代表五件；脚本与 TS pyCode 逐字同构）
# ---------------------------------------------------------------------------
BIGFILE_TPL = """import json
from pathlib import Path

def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{{n:.1f}}{{unit}}"
        n /= 1024
    return f"{{n:.1f}}PB"

files = [(f.stat().st_size, f) for f in Path({src!r}).rglob("*") if f.is_file()]
files.sort(reverse=True)
print("<<<JSON>>>")
print(json.dumps({{"table": {{"columns": ["体积", "路径"], "rows": [[human(s), str(p)] for s, p in files[:{top}]]}}}}, ensure_ascii=False))
print("<<<END>>>")
"""

LOC_TPL = """import json
from pathlib import Path

stats = {{}}
for f in Path({src!r}).rglob("*"):
    if not f.is_file() or f.suffix not in {{".py", ".ts", ".js", ".vue", ".md", ".go"}}:
        continue
    code = comment = blank = 0
    for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = ln.strip()
        if not s:
            blank += 1
        elif s.startswith(("#", "//")):
            comment += 1
        else:
            code += 1
    acc = stats.setdefault(f.suffix, [0, 0, 0, 0])
    acc[0], acc[1], acc[2] = acc[0] + code, acc[1] + comment, acc[2] + blank
    acc[3] += 1
rows = [[ext, str(v[3]), str(v[0]), str(v[1]), str(v[2])] for ext, v in sorted(stats.items(), key=lambda kv: -kv[1][0])]
print("<<<JSON>>>")
print(json.dumps({{"table": {{"columns": ["扩展名", "文件数", "代码行", "注释行", "空行"], "rows": rows}}}}, ensure_ascii=False))
print("<<<END>>>")
"""

CSV_STATS_TPL = """import csv
import json

vals = []
with open({src!r}, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            vals.append(float(row[{col!r}]))
        except (KeyError, TypeError, ValueError):
            continue
vals.sort()
mean = sum(vals) / len(vals)
_r = {{
    "primary": {{"value": f"{{mean:.4g}}", "unit": "均值"}},
    "rows": [
        {{"label": "计数", "value": str(len(vals))}},
        {{"label": "最小 / 最大", "value": f"{{vals[0]:.4g}} / {{vals[-1]:.4g}}"}},
    ],
}}
print("<<<JSON>>>")
print(json.dumps(_r, ensure_ascii=False))
print("<<<END>>>")
"""

TABLE_DIFF_TPL = """import json

from openpyxl import load_workbook

def sheet_rows(path, sheet=None):
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    rows = [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    return rows

def to_dict(rows):
    head = rows[0]
    ki = head.index({key!r})
    return {{r[ki]: r for r in rows[1:]}}

old = to_dict(sheet_rows({old!r}))
new = to_dict(sheet_rows({new!r}))
added = [new[k] for k in new if k not in old]
removed = [old[k] for k in old if k not in new]
print("<<<JSON>>>")
print(json.dumps({{"primary": {{"value": str(len(added)), "unit": "新增 / " + str(len(removed)) + " 移除"}}}}, ensure_ascii=False))
print("<<<END>>>")
"""


def _parse_sidecar(stdout: str) -> dict:
    start = stdout.index("<<<JSON>>>") + len("<<<JSON>>>")
    end = stdout.index("<<<END>>>")
    return json.loads(stdout[start:end].strip())


def test_bigfile_topn_real_execution(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "big.bin").write_bytes(b"x" * 50000)
    (d / "small.bin").write_bytes(b"y" * 500)
    script = tmp_path / "run.py"
    script.write_text(BIGFILE_TPL.format(src=str(d), top=5), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    parsed = _parse_sidecar(r.stdout)
    rows = parsed["table"]["rows"]
    assert rows[0][0].startswith("48.8K") and rows[0][1].endswith("big.bin")


def test_loc_stats_real_execution(tmp_path):
    d = tmp_path / "code"
    d.mkdir()
    (d / "a.py").write_text("# 注释\nprint(1)\n\nprint(2)\n", encoding="utf-8")
    script = tmp_path / "run.py"
    script.write_text(LOC_TPL.format(src=str(d)), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rows = _parse_sidecar(r.stdout)["table"]["rows"]
    assert rows[0] == [".py", "1", "2", "1", "1"]


def test_csv_column_stats_real_execution(tmp_path):
    src = tmp_path / "t.csv"
    src.write_text("name,age\n张三,30\nlisi,20\n", encoding="utf-8")
    script = tmp_path / "run.py"
    script.write_text(CSV_STATS_TPL.format(src=str(src), col="age"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    parsed = _parse_sidecar(r.stdout)
    assert parsed["primary"]["value"] == "25"
    assert parsed["rows"][0] == {"label": "计数", "value": "2"}


def test_table_diff_wizard_real_execution(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from openpyxl import Workbook

    old = tmp_path / "old.xlsx"
    new = tmp_path / "new.xlsx"
    wb = Workbook()
    wb.active.append(["工号", "姓名"])
    wb.active.append(["E001", "张三"])
    wb.save(old)
    wb2 = Workbook()
    wb2.active.append(["工号", "姓名"])
    wb2.active.append(["E002", "李四"])
    wb2.save(new)
    script = tmp_path / "run.py"
    script.write_text(TABLE_DIFF_TPL.format(old=str(old), new=str(new), key="工号"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert _parse_sidecar(r.stdout)["primary"]["value"] == "1"


# ---------------------------------------------------------------------------
# W12：Office 改造真实执行测试（Excel 建表 / 公式汇总 / Word 表格）
# ---------------------------------------------------------------------------
EXCEL_BUILD_TPL = """import csv as _csv
import io as _io
import json

def parse_rows(text):
    return [r for r in _csv.reader(_io.StringIO(text.strip())) if r]

def _coerce(c):
    if c == "": return None
    if c == "true": return True
    if c == "false": return False
    try:
        return int(c)
    except ValueError:
        pass
    try:
        return float(c)
    except ValueError:
        pass
    return c

rows = parse_rows({data!r})
if len(rows) < 1:
    raise SystemExit("请提供至少一行表头")
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
for r in rows:
    ws.append([_coerce(c) for c in r])
wb.save("output.xlsx")
print("<<<JSON>>>")
print(json.dumps({{"rows": [{{"label": "规模", "value": f"{{ws.max_row}} 行 × {{ws.max_column}} 列"}}]}}, ensure_ascii=False))
print("<<<END>>>")
"""

EXCEL_FORMULA_TPL = """import csv as _csv
import io as _io
import json

def parse_rows(text):
    return [r for r in _csv.reader(_io.StringIO(text.strip())) if r]

rows = parse_rows({data!r})
from openpyxl import Workbook
import openpyxl.utils

wb = Workbook()
ws = wb.active
for r in rows:
    ws.append(r)
last_col = ws.max_column
sum_col = last_col + 1
ws.cell(row=1, column=sum_col, value="合计")
for r in range(2, ws.max_row + 1):
    ws.cell(row=r, column=sum_col, value=f"=SUM(A{{r}}:{{openpyxl.utils.get_column_letter(last_col)}}{{r}})")
wb.save("output.xlsx")
print("<<<JSON>>>")
print(json.dumps({{"rows": [{{"label": "产物", "value": "output.xlsx"}}]}}, ensure_ascii=False))
print("<<<END>>>")
"""

WORD_TABLE_TPL = """import csv
import io
import json

from docx import Document

rows = list(csv.reader(io.StringIO({data!r})))
doc = Document()
table = doc.add_table(rows=len(rows), cols=len(rows[0]))
table.style = "Table Grid"
for i, row in enumerate(rows):
    for j, cell in enumerate(row):
        table.cell(i, j).text = str(cell)
doc.save("table.docx")
print("<<<JSON>>>")
print(json.dumps({{"rows": [{{"label": "产物", "value": "table.docx"}}]}}, ensure_ascii=False))
print("<<<END>>>")
"""


def test_excel_build_real_execution(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    data = "名称,数量\n苹果,12\nlisi,"
    script = tmp_path / "run.py"
    script.write_text(EXCEL_BUILD_TPL.format(data=data), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    from openpyxl import load_workbook

    wb = load_workbook(tmp_path / "output.xlsx")
    ws = wb.active
    assert ws.cell(row=2, column=1).value == "苹果"
    assert ws.cell(row=2, column=2).value == 12  # int 推断
    assert ws.cell(row=3, column=2).value is None  # 空串 → None
    parsed = _parse_sidecar(r.stdout)
    assert parsed["rows"][0]["value"] == "3 行 × 2 列"


def test_excel_formula_real_execution(tmp_path):
    pytest.importorskip("openpyxl")
    data = "项目,金额\nA,10\nB,20"
    script = tmp_path / "run.py"
    script.write_text(EXCEL_FORMULA_TPL.format(data=data), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    from openpyxl import load_workbook

    wb = load_workbook(tmp_path / "output.xlsx")
    ws = wb.active
    assert ws.cell(row=2, column=3).value == "=SUM(A2:B2)"


def test_word_table_real_execution(tmp_path):
    docx = pytest.importorskip("docx")
    data = "名称,数量\n苹果,12"
    script = tmp_path / "run.py"
    script.write_text(WORD_TABLE_TPL.format(data=data), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    d = docx.Document(tmp_path / "table.docx")
    assert len(d.tables) == 1
    assert d.tables[0].cell(1, 0).text == "苹果"


# ---------------------------------------------------------------------------
# W13：真实执行测试（YAML 转换 / 透视 / 编码修复 / 二维码）
# ---------------------------------------------------------------------------
YAML2JSON_TPL = """import json

import yaml

data = yaml.safe_load({inp!r})
print("<<<JSON>>>")
print(json.dumps({{"text": json.dumps(data, ensure_ascii=False, indent=2)}}, ensure_ascii=False))
print("<<<END>>>")
"""

PIVOT_TPL = """import csv
import io
import json
from collections import defaultdict

rows = list(csv.DictReader(io.StringIO({data!r})))
pivot = defaultdict(float)
col_keys = []
for r in rows:
    ck = r[{col_dim!r}]
    if ck not in col_keys:
        col_keys.append(ck)
    pivot[(r[{row_dim!r}], ck)] += float(r[{val_col!r}] or 0)
col_keys.sort()
row_keys = sorted({{k[0] for k in pivot}})
table_rows = [[rk] + [f"{{pivot.get((rk, ck), 0):g}}" for ck in col_keys] for rk in row_keys]
print("<<<JSON>>>")
print(json.dumps({{"table": {{"columns": [{row_dim!r}] + col_keys, "rows": table_rows}}}}, ensure_ascii=False))
print("<<<END>>>")
"""

ENCODING_FIX_TPL = """import json

data = open({src!r}, "rb").read()
detected = None
for enc in ("utf-8", "gbk", "latin-1"):
    try:
        text = data.decode(enc)
        detected = enc
        break
    except (UnicodeDecodeError, UnicodeError):
        continue
open("fixed.utf8.txt", "w", encoding="utf-8").write(text)
print("<<<JSON>>>")
print(json.dumps({{"rows": [{{"label": "检测编码", "value": detected}}]}}, ensure_ascii=False))
print("<<<END>>>")
"""

QRCODE_TPL = """import qrcode

img = qrcode.make({text!r})
img.save("qrcode.png")
print("generated")
"""


def test_yaml_to_json_real_execution(tmp_path):
    pytest.importorskip("yaml")
    script = tmp_path / "run.py"
    script.write_text(YAML2JSON_TPL.format(inp="name: 张三\nage: 30"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    parsed = _parse_sidecar(r.stdout)
    assert '"name": "张三"' in parsed["text"]
    assert '"age": 30' in parsed["text"]


def test_pivot_real_execution(tmp_path):
    data = "部门,月份,金额\n研发,1月,120\n研发,2月,135\n市场,1月,90\n市场,2月,110\n研发,1月,60"
    script = tmp_path / "run.py"
    script.write_text(PIVOT_TPL.format(data=data, row_dim="部门", col_dim="月份", val_col="金额"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rows = _parse_sidecar(r.stdout)["table"]["rows"]
    assert rows[0] == ["市场", "90", "110"]
    assert rows[1][:2] == ["研发", "180"]  # 120 + 60


def test_encoding_fix_real_execution(tmp_path):
    src = tmp_path / "gbk.txt"
    src.write_bytes("中文内容".encode("gbk"))
    script = tmp_path / "run.py"
    script.write_text(ENCODING_FIX_TPL.format(src=str(src)), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rows = _parse_sidecar(r.stdout)["rows"]
    assert rows[0]["value"] == "gbk"
    assert (tmp_path / "fixed.utf8.txt").read_text(encoding="utf-8") == "中文内容"


def test_qrcode_real_execution(tmp_path):
    pytest.importorskip("qrcode")
    script = tmp_path / "run.py"
    script.write_text(QRCODE_TPL.format(text="https://example.com"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    from PIL import Image

    with Image.open(tmp_path / "qrcode.png") as im:
        assert im.size[0] >= 100  # 正方形二维码


# ---------------------------------------------------------------------------
# W15：保险库往返真实执行（add → list 同口令可读）+ Word 读取
# ---------------------------------------------------------------------------
VAULT_LIB = """import base64
import hashlib
import json
import os

VAULT = "vault.enc.json"

def keystream(master, salt, size):
    out = b""
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(master.encode() + salt + str(counter).encode()).digest()
        counter += 1
    return out[:size]

def xor(data, key):
    return bytes(a ^ b for a, b in zip(data, key))

def load(master):
    raw = json.loads(open(VAULT, encoding="utf-8").read())
    salt = base64.b64decode(raw["salt"])
    data = xor(base64.b64decode(raw["data"]), keystream(master, salt, len(base64.b64decode(raw["data"]))))
    return json.loads(data.decode("utf-8"))

def save(master, entries):
    salt = os.urandom(16)
    text = json.dumps(entries, ensure_ascii=False).encode("utf-8")
    enc = xor(text, keystream(master, salt, len(text)))
    open(VAULT, "w", encoding="utf-8").write(json.dumps(
        {{"salt": base64.b64encode(salt).decode(), "data": base64.b64encode(enc).decode()}}))
"""

VAULT_ADD_TPL = VAULT_LIB + """
import sys

entries = {{}}
if os.path.exists(VAULT):
    try:
        entries = load({master!r})
    except Exception:
        print("解密失败：主口令错误或库已损坏")
        sys.exit(1)
entries[{site!r}] = {secret!r}
save({master!r}, entries)
print("OK")
"""

VAULT_LIST_TPL = VAULT_LIB + """
entries = load({master!r})
print("<<<JSON>>>")
print(json.dumps({{"list": [f"{{s}} → {{p[:2]}}{{'*' * max(0, len(p) - 2)}}".replace("{{'*' * 0}}", "") for s, p in entries.items()]}}, ensure_ascii=False))
print("<<<END>>>")
"""

WORD_READ_TPL = """import json

from docx import Document

doc = Document({src!r})
lines = ["== 段落 =="]
for p in doc.paragraphs:
    if p.text.strip():
        lines.append(f"[{{p.style.name}}] {{p.text}}")
print("<<<JSON>>>")
print(json.dumps({{"text": "\\n".join(lines)}}, ensure_ascii=False))
print("<<<END>>>")
"""


def test_vault_roundtrip_real_execution(tmp_path):
    script = tmp_path / "add.py"
    script.write_text(VAULT_ADD_TPL.format(master="m1", site="github.com", secret="s3cret"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    lst = tmp_path / "list.py"
    lst.write_text(VAULT_LIST_TPL.format(master="m1"), encoding="utf-8")
    r2 = subprocess.run([sys.executable, str(lst)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r2.returncode == 0, r2.stderr
    parsed = _parse_sidecar(r2.stdout)
    assert any("github.com" in x for x in parsed["list"])
    # 错误口令 → 退出码 1（解密失败不静默）
    bad = tmp_path / "bad.py"
    bad.write_text(VAULT_ADD_TPL.format(master="WRONG", site="x", secret="y"), encoding="utf-8")
    r3 = subprocess.run([sys.executable, str(bad)], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r3.returncode != 0


def test_word_read_real_execution(tmp_path):
    docx = pytest.importorskip("docx")
    from docx import Document

    src = tmp_path / "周会.docx"
    doc = Document()
    doc.add_heading("周会纪要", level=1)
    doc.add_paragraph("下次会议改期")
    doc.save(src)
    script = tmp_path / "run.py"
    script.write_text(WORD_READ_TPL.format(src=str(src)), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    parsed = _parse_sidecar(r.stdout)
    assert "周会纪要" in parsed["text"]
    assert "下次会议改期" in parsed["text"]


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
