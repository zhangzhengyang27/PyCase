"""API 签名：私有接口的标准鉴权构造。"""
import hashlib
import hmac
import time
from urllib.parse import urlencode

API_KEY, SECRET = "demo-key", "demo-secret"
params = {"symbol": "BTCUSDT", "timestamp": int(time.time() * 1000)}
query = urlencode(params)
sign = hmac.new(SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
print("待签名串:", query)
print("签名:", sign[:32], "...")
print("完整请求: /api/v1/order?" + query + "&signature=" + sign[:16] + "…")
