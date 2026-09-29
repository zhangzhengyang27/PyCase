"""超时与重试：指数退避，最多 4 次。"""
import time
import requests

URL = "https://httpbin.org/status/200,503"
for attempt in range(1, 5):
    try:
        resp = requests.get(URL, timeout=(3.05, 10))  # (连接, 读取)
        if resp.status_code == 200:
            print(f"第 {attempt} 次成功")
            break
        print(f"第 {attempt} 次状态码 {resp.status_code}")
    except requests.RequestException as e:
        print(f"第 {attempt} 次异常: {type(e).__name__}")
    time.sleep(2 ** attempt)  # 1, 2, 4 秒退避
else:
    print("重试耗尽，放弃")
