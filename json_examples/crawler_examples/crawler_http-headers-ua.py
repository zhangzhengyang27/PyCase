"""请求头构造：模拟 Chrome 浏览器发起请求。"""
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

resp = requests.get("https://httpbin.org/user-agent", headers=HEADERS, timeout=10)
print("服务端收到的 UA:", resp.json()["user-agent"])
print("状态码:", resp.status_code)
