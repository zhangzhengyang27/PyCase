"""apscheduler：后台定时抓取（演示跑一轮即退出）。"""
from apscheduler.schedulers.background import BackgroundScheduler

runs = []

def hourly_fetch():
    runs.append("fetch")

sched = BackgroundScheduler()
sched.add_job(hourly_fetch, "interval", seconds=1, id="hourly")
sched.start()
import time
time.sleep(2.5)
sched.shutdown()
print(f"2.5 秒内触发 {len(runs)} 次（真实场景设 hours=1）")
