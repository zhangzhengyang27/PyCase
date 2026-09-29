"""番茄钟：终端倒计时。"""
import argparse
import sys
import time


def countdown(minutes: int, label: str) -> None:
    total = minutes * 60
    for remain in range(total, 0, -1):
        mm, ss = divmod(remain, 60)
        sys.stdout.write(f"\r{label} 剩余 {mm:02d}:{ss:02d} ")
        sys.stdout.flush()
        time.sleep(1)
    print(f"\r{label} 完成！\a")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus", type=int, default=1, help="专注时长(分钟)，演示用默认 1")
    parser.add_argument("--break-mins", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    for i in range(1, args.rounds + 1):
        print(f"—— 第 {i}/{args.rounds} 轮 ——")
        countdown(args.focus, "专注")
        if i < args.rounds:
            countdown(args.break_mins, "休息")


if __name__ == "__main__":
    main()
