"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：超时与保护 ----
budget = 1

async def slow():
    await asyncio.sleep(5)
    return "永远等不到"

async def fast():
    await asyncio.sleep(0.1)
    return "快速任务完成"

async def main():
    t0 = time.monotonic()
    try:
        await asyncio.wait_for(slow(), timeout=budget)
    except asyncio.TimeoutError:
        print(f"慢任务在预算 {budget}s 内未完成 → 超时放弃（实际等了 %.1fs）" % (time.monotonic() - t0))
    print(await asyncio.wait_for(fast(), timeout=budget))

asyncio.run(main())
