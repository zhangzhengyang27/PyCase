"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：事件循环与阻塞 ----
async def ticker():
    for i in range(3):
        print(f"  tick {i} @ %.2fs" % (time.monotonic() - T0["t"]))
        await asyncio.sleep(0.2)

T0 = {"t": time.monotonic()}

async def main():
    tick = asyncio.create_task(ticker())
    await asyncio.sleep(0.1)
    print("非阻塞 sleep（循环未被卡住）:")
    time.sleep(0.5)
    print("time.sleep(0.5) 期间 tick 全停 → 阻塞了事件循环")
    await tick

asyncio.run(main())
