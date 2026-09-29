"""ID 生成：uuid4 / 短ID / 序列号。"""
import argparse
import secrets
import uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["uuid", "short", "serial"], default="uuid")
    ap.add_argument("-n", type=int, default=3)
    args = ap.parse_args()
    for _ in range(args.n):
        if args.mode == "uuid":
            print(uuid.uuid4())
        elif args.mode == "short":
            print(secrets.token_urlsafe(8))
        else:
            print(time_id := f"{__import__('time').strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}")


if __name__ == "__main__":
    main()
