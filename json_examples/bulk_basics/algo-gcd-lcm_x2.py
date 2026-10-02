"""GCD/LCM：多组数。"""
from math import gcd

def lcm(a, b):
    return a * b // gcd(a, b)

pairs = [(100, 75), (81, 27), (97, 89)]
for a, b in pairs:
    print(f"gcd({a}, {b}) = {gcd(a, b)},  lcm = {lcm(a, b)}")
