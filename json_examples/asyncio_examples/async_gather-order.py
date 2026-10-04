"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：gather 与完成顺序 ----
n = 4

async def job(i):
    delay = 0.5 - i * 0.1
    await asyncio.sleep(delay)
    return i

async def main():
    ordered = await asyncio.gather(*(job(i) for i in range(n)))
    print("gather 返回（提交序）:", ordered)
    dones = [await c for c in asyncio.as_completed([job(i) for i in range(n)])]
    print("as_completed（完成序）:", dones)

asyncio.run(main())
