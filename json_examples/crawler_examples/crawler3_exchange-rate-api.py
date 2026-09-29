"""汇率抓取：open.er-api.com 实时牌价。"""
import requests

resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
rates = resp.json()["rates"]
for cur in ("CNY", "EUR", "JPY", "HKD"):
    print(f"1 USD = {rates.get(cur, '?')} {cur}")
print("更新时间:", resp.json().get("time_last_update_utc"))
