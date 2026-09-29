"""二维码生成：python xxx.py '文本或链接' -o qr.png"""
import argparse

import qrcode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("-o", "--output", default="qrcode.png")
    args = ap.parse_args()
    img = qrcode.make(args.text)
    img.save(args.output)
    print(f"已生成 {args.output}（{img.size[0]}×{img.size[1]}）")


if __name__ == "__main__":
    main()
