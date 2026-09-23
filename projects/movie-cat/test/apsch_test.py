# -*- coding: utf-8 -*-
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime


def aps_test():
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


scheduler = BlockingScheduler() # 实例化
scheduler.add_job(func=aps_test, trigger="cron", second="*/5") # 每5秒执行一次
scheduler.start()
