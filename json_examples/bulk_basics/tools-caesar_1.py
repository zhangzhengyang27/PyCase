"""凯撒密码：移位 3。"""
def caesar(text, k):
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + k) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + k) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)

msg = "'The quick brown fox jumps over the lazy dog 2026'"
enc = caesar(msg, 3)
print("原文:", msg)
print("加密:", enc)
print("解密:", caesar(enc, -3))
