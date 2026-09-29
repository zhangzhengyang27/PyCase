"""FizzBuzz：20~80，2 的倍数输出 A，7 的倍数输出 B。"""
for n in range(20, 80 + 1):
    out = ""
    if n % 2 == 0:
        out += "A"
    if n % 7 == 0:
        out += "B"
    print(n, out or n)
