// tool-schemas-asyncio-lab.ts：并发与异步实验室（新域，10 类型 = 语料 asyncio_examples 一一对应母本）。
// 全部离线 stdlib（asyncio/queue/lock；aiohttp 仅一个类型用到且已入库），事件循环脚本有限轮次收尾。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const int = (v: unknown, def: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, Math.trunc(Number(v) || def)))

const ASYNCIO_HEAD = `"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time
`

const N = (key: string, label: string, def: number): FieldSpec => ({
  key,
  label,
  type: 'number',
  default: def,
  width: 'half'
})

export interface AsyncType {
  value: string
  label: string
  description: string
  fields?: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const at = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): AsyncType => ({ value, label, description, fields, body })

export const ASYNC_TYPES: AsyncType[] = [
  at(
    'async-basics',
    'async/await 入门',
    '顺序 await vs gather 并发：同两个 IO 任务的耗时对比。',
    [N('tasks', '任务数', 3)],
    (v) => `n = ${int(v.tasks, 3, 2, 6)}

async def job(i):
    await asyncio.sleep(0.3)
    return f"任务{i} 完成"

async def main():
    t0 = time.monotonic()
    for i in range(n):
        await job(i)
    seq = time.monotonic() - t0
    t0 = time.monotonic()
    results = await asyncio.gather(*(job(i) for i in range(n)))
    par = time.monotonic() - t0
    print("顺序:", results[0], "…耗时 %.2fs" % seq)
    print("并发:", results, "耗时 %.2fs" % par)
    print(f"提速约 {seq / par:.1f} 倍（IO 等待重叠）")

asyncio.run(main())`
  ),
  at(
    'gather-order',
    'gather 与完成顺序',
    'gather 保持提交顺序返回；as_completed 按完成先后消费。',
    [N('tasks', '任务数', 4)],
    (v) => `n = ${int(v.tasks, 4, 2, 6)}

async def job(i):
    delay = 0.5 - i * 0.1
    await asyncio.sleep(delay)
    return i

async def main():
    ordered = await asyncio.gather(*(job(i) for i in range(n)))
    print("gather 返回（提交序）:", ordered)
    dones = [await c for c in asyncio.as_completed([job(i) for i in range(n)])]
    print("as_completed（完成序）:", dones)

asyncio.run(main())`
  ),
  at(
    'sleep-timing',
    '事件循环与阻塞',
    'asyncio.sleep 让出循环 vs time.sleep 卡死循环：阻塞的代价一目了然。',
    [],
    () => `async def ticker():
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

asyncio.run(main())`
  ),
  at(
    'semaphore',
    '信号量限并发',
    'Semaphore 限制同时运行的任务数：并发有上限的下载池。',
    [N('limit', '并发上限', 2)],
    (v) => `limit = ${int(v.limit, 2, 1, 4)}
sem = asyncio.Semaphore(limit)
ACTIVE = {"n": 0}
PEAK = {"n": 0}

async def fetch(i):
    async with sem:
        ACTIVE["n"] += 1
        PEAK["n"] = max(PEAK["n"], ACTIVE["n"])
        await asyncio.sleep(0.2)
        ACTIVE["n"] -= 1
        return i

async def main():
    await asyncio.gather(*(fetch(i) for i in range(6)))
    print(f"6 个任务、并发上限 {limit} → 实测同时运行峰值 {PEAK['n']}")

asyncio.run(main())`
  ),
  at(
    'queue',
    '生产者消费者',
    'asyncio.Queue 解耦两端：多生产者投递、消费者池消化。',
    [N('producers', '生产者数', 2), N('consumers', '消费者数', 2)],
    (v) => `producers_n = ${int(v.producers, 2, 1, 3)}
nc = ${int(v.consumers, 2, 1, 3)}
queue = asyncio.Queue()
DONE = []

async def producer(pid):
    for i in range(3):
        await queue.put(f"p{pid}-任务{i}")

async def consumer(cid):
    while True:
        item = await queue.get()
        await asyncio.sleep(0.1)
        DONE.append(f"消费者{cid}:{item}")
        queue.task_done()

async def main():
    producers = [asyncio.create_task(producer(p)) for p in range(producers_n)]
    consumers = [asyncio.create_task(consumer(c)) for c in range(nc)]
    await asyncio.gather(*producers)
    await queue.join()
    for c in consumers:
        c.cancel()
    print(f"{producers_n} 生产者 × 3 任务 → {nc} 消费者共处理 {len(DONE)} 件:")
    print(DONE)

asyncio.run(main())`
  ),
  at(
    'task-cancel',
    '任务取消与异常',
    'create_task 的取消（CancelledError）与异常不会静默丢失。',
    [],
    () => `async def worker():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("worker 收到取消信号，做清理")
        raise

async def failing():
    await asyncio.sleep(0.05)
    raise RuntimeError("业务异常")

async def main():
    t = asyncio.create_task(worker())
    await asyncio.sleep(0.1)
    t.cancel()
    try:
        await t
    except asyncio.CancelledError:
        print("任务已取消")
    try:
        await failing()
    except RuntimeError as e:
        print("捕获任务异常:", e)

asyncio.run(main())`
  ),
  at(
    'aiohttp-fetch',
    'aiohttp 并发抓取',
    'ClientSession + gather 抓本地演示服务：异步 IO 的标准实战形态。',
    [N('pages', '并发请求数', 4)],
    (v) => `import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = "http://127.0.0.1:" + str(srv.server_address[1])

import aiohttp

n = ${int(v.pages, 4, 2, 8)}

async def fetch(session, i):
    async with session.get(base + f"/p{i}") as resp:
        return i, resp.status

async def main():
    async with aiohttp.ClientSession() as s:
        results = await asyncio.gather(*(fetch(s, i) for i in range(n)))
    print("并发抓取结果:", sorted(results))

asyncio.run(main())
srv.shutdown()`
  ),
  at(
    'to-thread',
    'to_thread 卸载阻塞',
    'asyncio.to_thread 把阻塞调用扔进线程池：不卡事件循环的两全法。',
    [],
    () => `def blocking_io():
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

asyncio.run(main())`
  ),
  at(
    'locks-events',
    '锁与事件',
    'asyncio.Lock 保护共享计数；Event 一键广播收尾信号。',
    [N('workers', '协程数', 4)],
    (v) => `n = ${int(v.workers, 4, 2, 6)}
counter = {"value": 0}
lock = asyncio.Lock()
event = asyncio.Event()

async def worker(i):
    for _ in range(100):
        async with lock:
            counter["value"] += 1
    print(f"worker{i} 完成")
    if i == n - 1:
        event.set()

async def main():
    await asyncio.gather(*(worker(i) for i in range(n)))
    await event.wait()
    print(f"加锁保护后计数无损: {counter['value']}（期望 {n * 100}）")

asyncio.run(main())`
  ),
  at(
    'timeout',
    '超时与保护',
    'wait_for 超时兜底：慢任务不许拖垮整批。',
    [N('seconds', '超时秒数', 1)],
    (v) => `budget = ${Math.min(2, Math.max(0.2, Number(v.seconds) || 1))}

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

asyncio.run(main())`
  )
]

const ASYNC_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '并发类型',
  type: 'select',
  default: 'async-basics',
  width: 'full',
  options: ASYNC_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const asyncioLabSchema: InteractiveToolSchema = {
  id: 'interactive:asyncio-lab',
  title: '并发与异步实验室',
  description:
    'asyncio 十个类型：入门对比/gather 完成序/事件循环阻塞/信号量/生产者消费者/取消与异常/aiohttp 并发/to_thread/锁与事件/超时保护，离线可跑。',
  tags: ['并发', 'asyncio'],
  fields: (v) => {
    const t = ASYNC_TYPES.find((x) => x.value === v.type) ?? ASYNC_TYPES[0]!
    return [ASYNC_TYPE_FIELD, ...(t.fields ?? [])]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '类型', value: String(v.type ?? 'async-basics') }] }),
  headerFor: (v) => {
    const t = ASYNC_TYPES.find((x) => x.value === v.type) ?? ASYNC_TYPES[0]!
    return { title: t.label, description: t.description }
  },
  pyCode: (v) => {
    const t = ASYNC_TYPES.find((x) => x.value === v.type) ?? ASYNC_TYPES[0]!
    return `${ASYNCIO_HEAD}\n# ---- 类型：${t.label} ----\n${t.body(v)}\n`
  }
}
