"""GCD/LCM：多组数。"""
from math import gcd

def lcm(a, b):
    return a * b // gcd(a, b)

pairs = [(270, 192), (1071, 462), (2026, 922)]
for a, b in pairs:
    print(f"gcd({a}, {b}) = {gcd(a, b)},  lcm = {lcm(a, b)}")
