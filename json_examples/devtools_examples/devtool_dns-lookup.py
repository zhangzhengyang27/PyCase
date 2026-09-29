"""DNS 查询：socket 标准库版。"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    args = ap.parse_args()
    try:
        infos = socket.getaddrinfo(args.domain, 443, socket.AF_INET)
        ips = sorted({info[4][0] for info in infos})
        print(f"{args.domain} -> {ips}")
    except socket.gaierror as e:
        print("解析失败:", e)
    try:
        print("规范名:", socket.gethostbyaddr(socket.gethostbyname(args.domain))[0])
    except socket.herror:
        pass


if __name__ == "__main__":
    main()
