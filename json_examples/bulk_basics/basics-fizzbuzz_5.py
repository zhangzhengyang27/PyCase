"""FizzBuzz：1~50，2 的倍数输出 A，7 的倍数输出 B。"""
for n in range(1, 50 + 1):
    out = ""
    if n % 2 == 0:
        out += "A"
    if n % 7 == 0:
        out += "B"
    print(n, out or n)
