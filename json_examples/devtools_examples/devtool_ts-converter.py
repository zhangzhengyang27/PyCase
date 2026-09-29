"""时间戳转换：now | <epoch> | --date '2026-01-01 10:00'"""
import argparse
from datetime import datetime


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value", nargs="?", default="now")
    ap.add_argument("--date", help="反向：日期字符串转时间戳")
    args = ap.parse_args()
    if args.date:
        dt = datetime.fromisoformat(args.date)
        print(int(dt.timestamp()))
    elif args.value == "now":
        now = datetime.now()
        print("时间戳:", int(now.timestamp()), "|", now.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        ts = int(args.value)
        print(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
