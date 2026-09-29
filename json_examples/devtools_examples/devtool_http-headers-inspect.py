"""响应头检查：缓存与安全配置一览。"""
import argparse
import requests

INTERESTING = ["Cache-Control", "Content-Type", "Content-Encoding", "Server",
               "Strict-Transport-Security", "Content-Security-Policy",
               "Access-Control-Allow-Origin", "ETag"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    args = ap.parse_args()
    resp = requests.get(args.url, timeout=10)
    print("状态:", resp.status_code)
    for h in INTERESTING:
        v = resp.headers.get(h)
        if v:
            print(f"  {h}: {v[:60]}")
    missing = [h for h in ("Strict-Transport-Security", "Content-Security-Policy") if h not in resp.headers]
    print("缺失安全头:", missing or "无")
