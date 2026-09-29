"""IP 查询：出口 IP 与服务商。"""
import requests

resp = requests.get("https://api.ipify.org?format=json", timeout=10)
ip = resp.json()["ip"]
print("出口 IP:", ip)
try:
    info = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10).json()
    print("归属:", info.get("country_name"), info.get("city"), info.get("org"))
except requests.RequestException:
    print("归属查询失败（不影响 IP 获取）")
