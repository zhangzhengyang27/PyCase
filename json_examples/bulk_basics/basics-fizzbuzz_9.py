"""FizzBuzz：10~60，4 的倍数输出 A，6 的倍数输出 B。"""
for n in range(10, 60 + 1):
    out = ""
    if n % 4 == 0:
        out += "A"
    if n % 6 == 0:
        out += "B"
    print(n, out or n)
