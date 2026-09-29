"""UA 池：每次请求随机挑一个身份。"""
import random
import requests

UA_POOL = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/126.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14) Chrome/125.0.0.0 Mobile",
]
for _ in range(3):
    ua = random.choice(UA_POOL)
    resp = requests.get("https://httpbin.org/user-agent",
                        headers={"User-Agent": ua}, timeout=10)
    print(resp.json()["user-agent"][:44])
