"""进制转换：十进制 4095 的各进制表示。"""
num = 4095
for base in [2, 8, 16, 32]:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    n = num
    while n:
        out = digits[n % base] + out
        n //= base
    print(f"base-{base:>2}: {out or '0'}")
