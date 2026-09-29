"""单位换算：python xxx.py 5 km mile | 100 f c"""
import argparse

LENGTH = {"m": 1, "km": 1000, "mile": 1609.344, "ft": 0.3048, "inch": 0.0254}
WEIGHT = {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.02835}
DATA = {"MB": 1, "KB": 1 / 1024, "GB": 1024, "TB": 1024 ** 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value", type=float)
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    v, src, dst = args.value, args.src.lower(), args.dst.lower()
    if {src, dst} <= set(LENGTH):
        print(f"{v * LENGTH[src] / LENGTH[dst]:.4f} {dst}")
    elif {src, dst} <= set(WEIGHT):
        print(f"{v * WEIGHT[src] / WEIGHT[dst]:.4f} {dst}")
    elif {src, dst} <= set(DATA):
        print(f"{v * DATA[src.upper()] / DATA[dst.upper()]:.4f} {dst.upper()}")
    elif src == "c" and dst == "f":
        print(f"{v * 9 / 5 + 32:.2f} °F")
    elif src == "f" and dst == "c":
        print(f"{(v - 32) * 5 / 9:.2f} °C")
    else:
        print("不支持的单位对")


if __name__ == "__main__":
    main()
