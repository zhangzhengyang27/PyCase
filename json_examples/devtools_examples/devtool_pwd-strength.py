"""密码强度：评分 0-100 与改进建议。"""
import argparse
import re

WEAK = {"password", "123456", "qwerty", "admin888", "111111", "abc123"}


def score(pwd):
    s = 0
    notes = []
    if len(pwd) >= 8: s += 20
    else: notes.append("长度不足 8 位")
    if len(pwd) >= 14: s += 15
    if re.search(r"[a-z]", pwd) and re.search(r"[A-Z]", pwd): s += 20
    else: notes.append("建议混合大小写")
    if re.search(r"\d", pwd): s += 20
    else: notes.append("建议包含数字")
    if re.search(r"[^\w]", pwd): s += 15
    else: notes.append("建议包含符号")
    if pwd.lower() in WEAK: return 0, ["常见弱口令，必须更换"]
    if not re.search(r"(.)\1{2,}", pwd): s += 10
    else: notes.append("避免连续重复字符")
    return min(100, s), notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("password")
    args = ap.parse_args()
    s, notes = score(args.password)
    level = "弱" if s < 40 else "中" if s < 70 else "强"
    print(f"强度: {s}/100（{level}）")
    for n in notes:
        print("  -", n)


if __name__ == "__main__":
    main()
