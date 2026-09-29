"""密码生成器：secrets 安全随机。"""
import argparse
import secrets
import string


def generate(length: int, symbols: bool) -> str:
    pool = string.ascii_letters + string.digits
    if symbols:
        pool += "!@#$%^&*"
    while True:
        pwd = "".join(secrets.choice(pool) for _ in range(length))
        # 保证至少含小写、大写、数字
        if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                and any(c.isdigit() for c in pwd)):
            return pwd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=16, help="密码长度")
    parser.add_argument("--symbols", action="store_true", help="包含特殊符号")
    args = parser.parse_args()
    for _ in range(3):
        print(generate(args.n, args.symbols))


if __name__ == "__main__":
    main()
