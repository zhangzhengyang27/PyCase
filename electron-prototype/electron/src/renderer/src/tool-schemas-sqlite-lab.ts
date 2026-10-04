// tool-schemas-sqlite-lab.ts：SQLite 数据库实验室（新域，10 类型 = 语料 sqlite_examples 一一对应母本）。
// 全部离线：stdlib sqlite3 建库演示（临时目录落盘 / :memory:），覆盖建表→参数化增查→改删→
// 聚合→连接→事务→索引→日期函数→CSV 批量导入 全链路。脚本运行结束清理临时文件。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '').trim()
const int = (v: unknown, def: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, Math.trunc(Number(v) || def)))

const SQLITE_HEAD = `"""（SQLite 实验室生成脚本：stdlib sqlite3，离线可跑，临时库自动清理）"""
import atexit
import os
import shutil
import sqlite3
import tempfile

workdir = tempfile.mkdtemp(prefix="sqlite-lab-")
atexit.register(shutil.rmtree, workdir, ignore_errors=True)
DB_PATH = os.path.join(workdir, "demo.db")
conn = sqlite3.connect(DB_PATH)
conn.execute(
    "CREATE TABLE goods (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT, price REAL, stock INTEGER DEFAULT 0)"
)
SEED = [
    (1, "机械键盘", "外设", 329.0, 12),
    (2, "无线鼠标", "外设", 149.0, 30),
    (3, "显示器", "显示", 1299.0, 6),
    (4, "USB-C 扩展坞", "配件", 259.0, 18),
    (5, "笔记本支架", "配件", 89.0, 25),
]
conn.executemany("INSERT INTO goods VALUES (?, ?, ?, ?, ?)", SEED)
conn.commit()
`

const N = (key: string, label: string, def: number): FieldSpec => ({
  key,
  label,
  type: 'number',
  default: def,
  width: 'half'
})
const SEL = (key: string, label: string, def: string, opts: string[]): FieldSpec => ({
  key,
  label,
  type: 'select',
  default: def,
  width: 'half',
  options: opts.map((o) => ({ value: o, label: o }))
})

export interface SqliteType {
  value: string
  label: string
  description: string
  fields?: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const st = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): SqliteType => ({ value, label, description, fields, body })

export const SQLITE_TYPES: SqliteType[] = [
  st(
    'create-table',
    '建表与约束',
    'CREATE TABLE 的主键/非空/默认值约束，sqlite_master 反查表结构。',
    [],
    () => `for row in conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='goods'"):
    print(row[0])
cols = conn.execute("PRAGMA table_info(goods)").fetchall()
print("\\n字段:")
for c in cols:
    print(f"  {c[1]} {c[2]} pk={c[5]} default={c[4]}")`
  ),
  st(
    'insert-query',
    '参数化插入与查询',
    '?占位符参数化插入（防注入）与 fetchone/fetchall 游标读取。',
    [N('id', '查询商品 id', 3)],
    (v) => `conn.execute("INSERT INTO goods VALUES (?, ?, ?, ?, ?)", (6, "摄像头", "外设", 399.0, 8))
conn.commit()
gid = ${int(v.id, 3, 1, 6)}
row = conn.execute("SELECT name, price FROM goods WHERE id = ?", (gid,)).fetchone()
print("按 id 查询:", row)
print("全部商品:")
for r in conn.execute("SELECT id, name, price FROM goods ORDER BY id"):
    print(" ", r)
print("总数:", conn.execute("SELECT COUNT(*) FROM goods").fetchone()[0])`
  ),
  st(
    'update-delete',
    '更新与删除',
    'UPDATE/DELETE 的 WHERE 条件与 rowcount 影响行数，安全清库演示。',
    [N('discount', '折扣（0-1）', 0.8)],
    (v) => `d = ${Math.min(0.95, Math.max(0.1, Number(v.discount) || 0.8))}
cur = conn.execute("UPDATE goods SET price = ROUND(price * ?, 1) WHERE category = '外设'", (d,))
print(f"外设打折 ×{d}，影响 {cur.rowcount} 行")
conn.commit()
cur2 = conn.execute("DELETE FROM goods WHERE stock < ?", (10,))
print(f"删除库存<10：{cur2.rowcount} 行")
conn.commit()
print("剩余:")
for r in conn.execute("SELECT id, name, price, stock FROM goods"):
    print(" ", r)`
  ),
  st(
    'aggregate',
    '分组聚合',
    'GROUP BY / HAVING / ORDER BY：SQL 侧聚合与过滤。',
    [N('min_total', 'HAVING 总值下限', 1000)],
    (v) => `floor = ${int(v.min_total, 1000, 0, 5000)}
sql = """
SELECT category, COUNT(*) AS cnt, ROUND(SUM(price * stock), 1) AS total
FROM goods GROUP BY category HAVING SUM(price * stock) > ? ORDER BY total DESC
"""
print(f"HAVING 库存总值 > {floor}:")
for r in conn.execute(sql, (floor,)):
    print(" ", r)
print("\\n全局极值:")
print(conn.execute("SELECT MAX(price), MIN(price), ROUND(AVG(price),1) FROM goods").fetchone())`
  ),
  st(
    'join',
    '两表连接',
    'INNER/LEFT JOIN 差异：无库存记录的品类如何去留。',
    [SEL('kind', '连接方式', 'LEFT', ['INNER', 'LEFT'])],
    (v) => `conn.execute("CREATE TABLE stock_notes (category TEXT PRIMARY KEY, note TEXT)")
conn.executemany("INSERT INTO stock_notes VALUES (?, ?)", [("外设", "热卖"), ("显示", "高客单")])
conn.commit()
kind = ${JSON.stringify(str(v.kind) || 'LEFT')}
sql = f"""
SELECT g.name, g.category, s.note FROM goods g {kind} JOIN stock_notes s ON g.category = s.category
"""
print(f"{kind} JOIN 结果:")
for r in conn.execute(sql):
    print(" ", r)
print("\\nLEFT 保留无备注品类（note=NULL），INNER 会丢弃")`
  ),
  st(
    'transactions',
    '事务与回滚',
    'commit/rollback：转账式两步操作的原子性演示。',
    [],
    () => `try:
    conn.execute("UPDATE goods SET stock = stock - 2 WHERE id = 1")
    conn.execute("UPDATE goods SET stock = stock + 2 WHERE id = 2")
    conn.execute("UPDATE goods SET stock = 库存 WHERE id = 3")  # 故意写错列名
    conn.commit()
except sqlite3.OperationalError as e:
    conn.rollback()
    print("出错回滚:", e)
after = conn.execute("SELECT id, stock FROM goods WHERE id IN (1, 2)").fetchall()
print("回滚后库存（1/2 号应保持 12/30）:", after)
conn.execute("UPDATE goods SET stock = stock - 2 WHERE id = 1")
conn.execute("UPDATE goods SET stock = stock + 2 WHERE id = 2")
conn.commit()
print("正常提交后:", conn.execute("SELECT id, stock FROM goods WHERE id IN (1, 2)").fetchall())`
  ),
  st(
    'index-explain',
    '索引与查询计划',
    '建索引前后 EXPLAIN QUERY PLAN 对比：全表扫描 → 索引查找。',
    [],
    () => `def plan(sql):
    return [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql)]

q = "SELECT * FROM goods WHERE name = '显示器'"
print("建索引前:", plan(q))
conn.execute("CREATE INDEX idx_goods_name ON goods(name)")
print("建索引后:", plan(q))
print("\\nSEARCH … USING INDEX = 走索引；SCAN = 全表扫描")`
  ),
  st(
    'in-memory',
    '内存库与游标',
    ':memory: 库、executemany 批量、fetchmany 分批读取。',
    [N('batch', '每批行数', 3)],
    (v) => `mem = sqlite3.connect(":memory:")
mem.execute("CREATE TABLE t (n INTEGER)")
mem.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(1, 11)])
cur = mem.execute("SELECT n FROM t")
batch = ${int(v.batch, 3, 1, 10)}
while rows := cur.fetchmany(batch):
    print("一批:", [r[0] for r in rows])
print("聚合:", mem.execute("SELECT SUM(n), AVG(n) FROM t").fetchone())`
  ),
  st(
    'date-functions',
    '日期函数',
    'date()/strftime()/julianday：SQL 侧时间处理与区间过滤。',
    [],
    () => `conn.execute("CREATE TABLE logs (id INTEGER PRIMARY KEY, event TEXT, ts TEXT)")
conn.executemany(
    "INSERT INTO logs (event, ts) VALUES (?, datetime('now', ?))",
    [("启动", "-3 days"), ("登录", "-1 hours"), ("下单", "-10 minutes"), ("支付", "0 minutes")],
)
conn.commit()
print("最近 1 天的事件:")
for r in conn.execute("SELECT event, ts FROM logs WHERE ts >= datetime('now', '-1 day') ORDER BY ts"):
    print(" ", r)
print("\\n按日期分组:")
for r in conn.execute("SELECT date(ts), COUNT(*) FROM logs GROUP BY date(ts)"):
    print(" ", r)`
  ),
  st(
    'csv-import',
    'CSV 批量导入导出',
    'csv → executemany 批量入库 → 查询导出，文件与库的双向通道。',
    [],
    () => `import csv
import io

CSV_TEXT = "name,category,price,stock\\n桌面音箱,外设,269,9\\n网线,配件,19,100\\n"
reader = csv.DictReader(io.StringIO(CSV_TEXT))
rows = [(r["name"], r["category"], float(r["price"]), int(r["stock"])) for r in reader]
conn.executemany("INSERT INTO goods (name, category, price, stock) VALUES (?, ?, ?, ?)", rows)
conn.commit()
out = io.StringIO()
w = csv.writer(out)
w.writerow(["name", "price"])
for r in conn.execute("SELECT name, price FROM goods WHERE category = '配件'"):
    w.writerow(r)
print("配件导出 CSV:")
print(out.getvalue().strip())
print("库内总行数:", conn.execute("SELECT COUNT(*) FROM goods").fetchone()[0])`
  )
]

const SQLITE_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '数据库类型',
  type: 'select',
  default: 'create-table',
  width: 'full',
  options: SQLITE_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const sqliteLabSchema: InteractiveToolSchema = {
  id: 'interactive:sqlite-lab',
  title: 'SQLite 数据库实验室',
  description:
    'stdlib sqlite3 十个类型：建表约束/参数化增查/更新删除/聚合/连接/事务回滚/索引计划/内存库/日期函数/CSV 导入导出，临时库离线可跑。',
  tags: ['数据库', 'sqlite'],
  fields: (v) => {
    const t = SQLITE_TYPES.find((x) => x.value === v.type) ?? SQLITE_TYPES[0]!
    return [SQLITE_TYPE_FIELD, ...(t.fields ?? [])]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '类型', value: String(v.type ?? 'create-table') }] }),
  headerFor: (v) => {
    const t = SQLITE_TYPES.find((x) => x.value === v.type) ?? SQLITE_TYPES[0]!
    return { title: t.label, description: t.description }
  },
  pyCode: (v) => {
    const t = SQLITE_TYPES.find((x) => x.value === v.type) ?? SQLITE_TYPES[0]!
    return `${SQLITE_HEAD}\n# ---- 类型：${t.label} ----\n${t.body(v)}\n`
  }
}
