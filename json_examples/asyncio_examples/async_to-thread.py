"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：to_thread 卸载阻塞 ----
def blocking_io():
    time.sleep(0.4)
    return "阻塞任务完成"

async def ticker():
    ticks = 0
    while not DONE["ok"]:
        ticks += 1
        await asyncio.sleep(0.1)
    return ticks

DONE = {"ok": False}

async def main():
    tick_task = asyncio.create_task(ticker())
    result = await asyncio.to_thread(blocking_io)
    DONE["ok"] = True
    print(result, "｜期间事件循环仍跳动", await tick_task, "次")

asyncio.run(main())
