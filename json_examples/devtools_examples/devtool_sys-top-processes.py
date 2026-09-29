"""进程榜：CPU 与内存 Top10。"""
import argparse

import psutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--by", choices=["cpu", "mem"], default="cpu")
    args = ap.parse_args()
    import time
    procs = list(psutil.process_iter(["pid", "name"]))
    for p in procs:
        try:
            p.cpu_percent(interval=None)  # 首次调用置零，建立采样基线
        except psutil.Error:
            pass
    time.sleep(0.5)
    for p in procs:
        try:
            p.info["cpu_percent"] = p.cpu_percent(interval=None)
            p.info["memory_percent"] = p.memory_percent()
        except psutil.Error:
            p.info["cpu_percent"] = p.info["memory_percent"] = 0.0
    key = (lambda p: p.info["memory_percent"] or 0) if args.by == "mem" else (lambda p: p.info["cpu_percent"] or 0)
    for p in sorted(procs, key=key, reverse=True)[:10]:
        print(f"{p.info['pid']:>7}  {p.info['name'][:26]:<26} "
              f"CPU {p.info['cpu_percent'] or 0:5.1f}%  MEM {p.info['memory_percent'] or 0:5.1f}%")


if __name__ == "__main__":
    main()
