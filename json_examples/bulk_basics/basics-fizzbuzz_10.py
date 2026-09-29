"""FizzBuzz：20~80，3 的倍数输出 A，5 的倍数输出 B。"""
for n in range(20, 80 + 1):
    out = ""
    if n % 3 == 0:
        out += "A"
    if n % 5 == 0:
        out += "B"
    print(n, out or n)
