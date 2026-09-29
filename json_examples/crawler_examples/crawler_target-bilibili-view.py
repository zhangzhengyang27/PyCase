"""B 站视频信息：公开 view 接口（BV 号解析）。"""
import re
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
           "Referer": "https://www.bilibili.com/"}

def fetch_bv(bvid):
    resp = requests.get("https://api.bilibili.com/x/web-interface/view",
                        params={"bvid": bvid}, headers=HEADERS, timeout=10)
    code = resp.json().get("code")
    if code != 0:
        return None
    d = resp.json()["data"]
    return {"标题": d["title"], "播放": d["stat"]["view"],
            "弹幕": d["stat"]["danmaku"], "UP主": d["owner"]["name"]}

if __name__ == "__main__":
    url = "https://www.bilibili.com/video/BV1GJ411x7h7/"
    bvid = re.search(r"(BV[0-9A-Za-z]{10})", url).group(1)
    info = fetch_bv(bvid)
    print(info or "接口不可达（网络环境限制时属正常）")
