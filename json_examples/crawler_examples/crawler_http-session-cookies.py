"""Session 会话：Cookie 在多次请求间自动保持。"""
import requests

with requests.Session() as s:
    s.headers["User-Agent"] = "Mozilla/5.0 (learning-demo)"
    s.get("https://httpbin.org/cookies/set/token/abc123", timeout=10)  # 服务端 Set-Cookie
    data = s.get("https://httpbin.org/cookies", timeout=10).json()
    print("会话内 Cookie:", data["cookies"])  # token 自动回传
