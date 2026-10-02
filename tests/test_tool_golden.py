"""交互工具黄金用例参考实现自校验（TS ↔ Python 对拍的 Python 侧）。

tool-golden.json 是双端唯一事实：expected 由本文件的 datetime 参考实现计算并在此
断言（防手改漂移）；TS 侧由 vitest（src/__tests__/tool-golden.spec.ts）断言
tool-schemas.ts 的 compute 输出与同一文件一致。改口径的顺序：先改参考实现并重算
JSON，再同步 TS schema，双侧测试同时转绿。
"""

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


def test_golden_has_all_sections():
    data = _load()
    assert len(data["temp"]) == 7
    assert len(data["base"]) == 8
    assert len(data["caesar"]) == 7
