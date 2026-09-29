"""颜色转换：#3498db rgb | 52,152,219 hex"""
import argparse
import colorsys


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#%02x%02x%02x" % rgb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value")
    args = ap.parse_args()
    v = args.value
    if v.startswith("#"):
        rgb = hex2rgb(v)
        h, l, s = colorsys.rgb_to_hls(*[x / 255 for x in rgb])
        print(f"RGB: {rgb}  HSL: ({h * 360:.0f}, {s * 100:.0f}%, {l * 100:.0f}%)")
    elif "," in v:
        rgb = tuple(int(x) for x in v.split(","))
        h, l, s = colorsys.rgb_to_hls(*[x / 255 for x in rgb])
        print(f"HEX: {rgb2hex(rgb)}  HSL: ({h * 360:.0f}, {s * 100:.0f}%, {l * 100:.0f}%)")
    else:
        print("输入 #hex 或 r,g,b")


if __name__ == "__main__":
    main()
