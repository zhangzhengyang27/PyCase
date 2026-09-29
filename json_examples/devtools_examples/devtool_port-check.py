"""端口检查：socket 探测目标主机端口列表。"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host")
    ap.add_argument("--ports", nargs="*", type=int, default=[80, 443, 22, 3306, 6379])
    ap.add_argument("--timeout", type=float, default=1.5)
    args = ap.parse_args()
    for port in args.ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(args.timeout)
            result = s.connect_ex((args.host, port)) == 0
        print(f"{args.host}:{port:<6} {'开放' if result else '关闭'}")


if __name__ == "__main__":
    main()
