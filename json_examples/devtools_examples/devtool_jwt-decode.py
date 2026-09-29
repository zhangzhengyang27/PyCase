"""JWT 解码：base64 分段解码（不验证签名）。"""
import argparse
import base64
import json
from datetime import datetime


def b64d(seg):
    return json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("token")
    args = ap.parse_args()
    header, payload, _ = args.token.split(".")
    h, p = b64d(header), b64d(payload)
    print("Header:", json.dumps(h, ensure_ascii=False, indent=1))
    print("Payload:", json.dumps(p, ensure_ascii=False, indent=1))
    if "exp" in p:
        exp = datetime.fromtimestamp(p["exp"])
        print("过期时间:", exp, "（已过期)" if exp < datetime.now() else "（有效）")


if __name__ == "__main__":
    main()
