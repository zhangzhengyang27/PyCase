"""FizzBuzz：1~30，4 的倍数输出 A，6 的倍数输出 B。"""
for n in range(1, 30 + 1):
    out = ""
    if n % 4 == 0:
        out += "A"
    if n % 6 == 0:
        out += "B"
    print(n, out or n)
