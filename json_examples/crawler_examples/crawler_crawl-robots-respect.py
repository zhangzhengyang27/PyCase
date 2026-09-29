"""robots.txt：抓取前先读规则。"""
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def can_fetch(url, ua="*"):
    rp = RobotFileParser()
    rp.set_url(f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt")
    try:
        rp.read()
    except Exception as e:
        print("robots.txt 读取失败（默认允许）:", type(e).__name__)
        return True
    return rp.can_fetch(ua, url)

for u in ["https://www.baidu.com/s?wd=python", "https://httpbin.org/get"]:
    print(u[:40], "可抓取" if can_fetch(u) else "被 robots 禁止")
