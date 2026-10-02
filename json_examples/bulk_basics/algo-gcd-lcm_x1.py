"""GCD/LCM：多组数。"""
from math import gcd

def lcm(a, b):
    return a * b // gcd(a, b)

pairs = [(12, 18), (24, 36), (48, 60)]
for a, b in pairs:
    print(f"gcd({a}, {b}) = {gcd(a, b)},  lcm = {lcm(a, b)}")
