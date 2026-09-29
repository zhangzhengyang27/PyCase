"""定时任务：sched 延时执行一次。"""
import sched
import time

scheduler = sched.scheduler(time.time, time.sleep)

def task(name):
    print(f"[{time.strftime('%H:%M:%S')}] 执行任务: {name}")

print("当前:", time.strftime("%H:%M:%S"))
scheduler.enter(2, 1, task, ("每日数据同步",))
scheduler.enter(4, 1, task, ("清理临时文件",))
scheduler.run()
print("队列执行完毕")
