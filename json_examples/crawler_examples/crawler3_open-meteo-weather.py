"""Open-Meteo：上海 7 天天气预报（免费无需 key）。"""
import requests

resp = requests.get("https://api.open-meteo.com/v1/forecast",
                    params={"latitude": 31.23, "longitude": 121.47,
                            "daily": "temperature_2m_max,temperature_2m_min",
                            "timezone": "Asia/Shanghai"}, timeout=10)
daily = resp.json()["daily"]
for d, tmax, tmin in zip(daily["time"], daily["temperature_2m_max"], daily["temperature_2m_min"]):
    print(f"{d}  {tmin}~{tmax}°C")
