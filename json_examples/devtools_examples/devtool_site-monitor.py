"""站点监控：循环探测 + 告警落盘。"""
import argparse
import time
from pathlib import Path
import requests

SITES = ["https://httpbin.org/status/200", "https://api.github.com"]


def check(url):
    try:
        return requests.get(url, timeout=8).status_code, None
    except requests.RequestException as e:
        return 0, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--interval", type=int, default=5)
    args = ap.parse_args()
    log = Path("monitor.log")
    for r in range(args.rounds):
        for url in SITES:
            code, err = check(url)
            line = f"{time.strftime('%H:%M:%S')} {url} -> {code or err}"
            print(line)
            if code >= 400 or err:
                with log.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")
        time.sleep(args.interval)
    print("告警日志:", log if log.exists() else "（无告警）")
