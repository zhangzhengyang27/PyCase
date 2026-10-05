// tool-schemas-pandas-lab.ts：数据分析实验室（pandas 新域，20 类型 = 语料 pandas_examples 一一对应母本）。
// 全部离线：内置三套演示数据集（订单 / 学生成绩 / 气温，固定种子生成），类型覆盖
// 读取→筛选→聚合→透视→连接→清洗→时间→导出→绘图 全链路；导出/绘图类型落盘真实产物。
// 语料 .py 母本由 pyCode 默认参数生成（与 bulk_* ↔ 实验室同构），卡进「数据分析」标签分区。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '').trim()
const int = (v: unknown, def: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, Math.trunc(Number(v) || def)))

const PANDAS_HEAD = `"""（数据分析实验室生成脚本：内置演示数据，离线可跑）"""
import io

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

ORDERS_CSV = """order_id,city,category,amount,qty,order_date
1,北京,键盘,199,1,2025-09-01
2,上海,鼠标,99,2,2025-09-01
3,北京,显示器,999,1,2025-09-02
4,广州,键盘,219,3,2025-09-02
5,上海,显示器,1299,1,2025-09-03
6,广州,鼠标,89,5,2025-09-03
7,北京,鼠标,109,2,2025-09-04
8,上海,键盘,189,1,2025-09-05
9,广州,显示器,899,2,2025-09-05
10,北京,键盘,239,2,2025-09-06
11,上海,鼠标,95,4,2025-09-06
12,广州,键盘,205,1,2025-09-07
13,北京,显示器,1099,1,2025-09-08
14,上海,键盘,179,2,2025-09-08
15,广州,鼠标,105,3,2025-09-09
"""

STUDENTS_CSV = """name,class,chinese,math,english
 张三 ,1班,88,92,85
李四,1班,76,,91
王五,2班,95,89,94
 赵六 ,2班,,66,72
钱七,1班,82,95,
孙八,2班,91,93,88
"""

# 由 rng 生成：60 天 × 北京/上海 的温度湿度
_w = pd.date_range("2025-08-01", periods=60, freq="D")
WEATHER = pd.DataFrame(
    {
        "date": _w.repeat(2),
        "city": ["北京", "上海"] * 60,
        "temp": np.concatenate([20 + 6 * np.sin(np.arange(60) / 6) + rng.normal(0, 1.5, 60),
                                26 + 5 * np.sin(np.arange(60) / 5) + rng.normal(0, 1.5, 60)]).round(1),
        "humidity": np.concatenate([rng.integers(35, 70, 60), rng.integers(55, 90, 60)]),
    }
)
`

const N = (key: string, label: string, def: number, help?: string): FieldSpec => ({
  key,
  label,
  type: 'number',
  default: def,
  width: 'half',
  ...(help ? { help } : {})
})
const SEL = (key: string, label: string, def: string, opts: string[]): FieldSpec => ({
  key,
  label,
  type: 'select',
  default: def,
  width: 'half',
  options: opts.map((o) => ({ value: o, label: o }))
})

export interface PandasType {
  value: string
  label: string
  description: string
  fields?: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const pt = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): PandasType => ({ value, label, description, fields, body })

export const PANDAS_TYPES: PandasType[] = [
  pt(
    'read-csv',
    'CSV 读取与预览',
    'read_csv 入门：head/dtypes/shape 三板斧快速摸底数据。',
    [N('rows', '预览行数', 5)],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
print(df.head(${int(v.rows, 5, 1, 15)}))
print("\\n形状:", df.shape)
print("\\n各列类型:")
print(df.dtypes)`
  ),
  pt(
    'select-filter',
    '列选择与行筛选',
    '列选取 / 布尔掩码 / query 三种筛选写法。',
    [SEL('city', '城市', '北京', ['北京', '上海', '广州']), N('min_amount', '金额下限', 100)],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
city = ${JSON.stringify(str(v.city) || '北京')}
low = ${int(v.min_amount, 100, 0, 5000)}
print("单列:", df["city"].tolist()[:6])
print("\\n布尔掩码（" + city + " 且金额>=" + str(low) + "）:")
print(df[(df["city"] == city) & (df["amount"] >= low)])
print("\\nquery 等价写法:")
print(df.query("city == @city and amount >= @low")[["order_id", "amount"]])`
  ),
  pt(
    'sort-top',
    '排序与 TopN',
    'sort_values 单列/多列排序与 nlargest 快速 TopN。',
    [N('top', 'TopN', 3), SEL('by', '排序依据', '金额', ['金额', '数量'])],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
col = {"金额": "amount", "数量": "qty"}[${JSON.stringify(str(v.by) || '金额')}]
top = ${int(v.top, 3, 1, 10)}
print(f"按 {col} 降序 Top{top}:")
print(df.nlargest(top, col)[["order_id", "city", "category", col]])
print("\\n多列排序（城市升序 + 金额降序）:")
print(df.sort_values(["city", "amount"], ascending=[True, False]).head(5))`
  ),
  pt(
    'groupby-agg',
    '分组聚合',
    'groupby + agg 命名聚合：一次拿到总和/均值/计数。',
    [SEL('group', '分组维度', '城市', ['城市', '品类'])],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
by = {"城市": "city", "品类": "category"}[${JSON.stringify(str(v.group) || '城市')}]
result = df.groupby(by).agg(
    总金额=("amount", "sum"),
    均价=("amount", "mean"),
    单数=("order_id", "count"),
).round(2).sort_values("总金额", ascending=False)
print(result)`
  ),
  pt(
    'pivot',
    '透视表',
    'pivot_table 交叉汇总：城市 × 品类的金额矩阵与 margins 合计。',
    [],
    () => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
pv = df.pivot_table(index="city", columns="category", values="amount",
                    aggfunc="sum", fill_value=0, margins=True, margins_name="合计")
print(pv)`
  ),
  pt(
    'merge-join',
    '表连接',
    'merge 内连接/左连接差异：连接键不匹配行的去留。',
    [SEL('how', '连接方式', 'left', ['inner', 'left'])],
    (v) => `orders = pd.read_csv(io.StringIO(ORDERS_CSV)).head(8)
prices = pd.DataFrame({"category": ["键盘", "鼠标", "摄像头"], "cost": [120, 45, 210]})
how = ${JSON.stringify(str(v.how) || 'left')}
merged = orders.merge(prices, on="category", how=how)
print(f"{how} 连接 → {len(merged)} 行（orders {len(orders)} 行）")
print(merged[["order_id", "category", "amount", "cost"]])
print("\\n左连接保留无价目的订单（cost=NaN），内连接会丢掉它们")`
  ),
  pt(
    'missing-data',
    '缺失值处理',
    'isna 定位 → 三种策略：填 0 / 填均值 / 丢行。',
    [SEL('strategy', '处理策略', '均值', ['填0', '均值', '丢行'])],
    (v) => `df = pd.read_csv(io.StringIO(STUDENTS_CSV))
print("各列缺失数:")
print(df.isna().sum())
strategy = ${JSON.stringify(str(v.strategy) || '均值')}
if strategy == "填0":
    out = df.fillna({"chinese": 0, "math": 0, "english": 0})
elif strategy == "丢行":
    out = df.dropna(subset=["math"])
else:
    out = df.fillna({"math": int(df["math"].mean()), "english": int(df["english"].mean())})
print(f"\\n{strategy} 后:")
print(out)`
  ),
  pt(
    'dtypes-cast',
    '类型转换',
    '脏类型纠正：字符串数字 to_numeric 容错转换与 astype。',
    [],
    () => `dirty = pd.DataFrame({"amount": ["199", "99", "缺", "899"], "qty": ["1", "2", "3", "2"]})
print("转换前 dtypes:")
print(dirty.dtypes)
dirty["amount"] = pd.to_numeric(dirty["amount"], errors="coerce")
dirty["qty"] = dirty["qty"].astype(int)
print("\\n转换后（无法解析的金额变 NaN）:")
print(dirty)
print("\\n有效金额均值:", dirty["amount"].mean().round(1))`
  ),
  pt(
    'apply',
    'apply 自定义函数',
    'axis=1 行级 apply 派生等级列，map 做字典映射。',
    [N('high', '高价阈值', 500)],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
high = ${int(v.high, 500, 50, 2000)}
def tier(amount):
    return "高价" if amount >= high else "中价" if amount >= 100 else "低价"

df["tier"] = df["amount"].apply(tier)
df["city_en"] = df["city"].map({"北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou"})
print(df[["amount", "tier", "city", "city_en"]].head(8))
print("\\n等级分布:")
print(df["tier"].value_counts())`
  ),
  pt(
    'string-methods',
    '字符串列处理',
    '.str 向量化字符串操作：去空白 / 提取 / 替换。',
    [],
    () => `df = pd.read_csv(io.StringIO(STUDENTS_CSV))
df["name"] = df["name"].str.strip()
df["class_no"] = df["class"].str.extract(r"(\\d)").astype(int)
df["class"] = df["class"].str.replace("班", "组", regex=False)
print(df[["name", "class", "class_no"]])
print("\\n含'王'的姓名:", df.loc[df["name"].str.contains("王"), "name"].tolist())`
  ),
  pt(
    'datetime-resample',
    '时间解析与重采样',
    'to_datetime + resample：日粒度转周粒度统计。',
    [],
    () => `w = WEATHER.copy()
w["date"] = pd.to_datetime(w["date"])
w = w.set_index("date")
weekly = w.groupby("city").resample("W")["temp"].mean().round(1)
print("周均温（每城前 3 周）:")
print(weekly.groupby(level=0).head(3))
bj = w[w["city"] == "北京"]
print("\\n北京 7 日移窗均温（末 5 天）:")
print(bj["temp"].rolling(7).mean().round(1).tail(5))`
  ),
  pt(
    'describe-stats',
    '描述统计与相关性',
    'describe 全景 + 数值列相关矩阵，一分钟摸清分布。',
    [],
    () => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
print(df[["amount", "qty"]].describe().round(1))
print("\\n金额与数量的相关系数:", df["amount"].corr(df["qty"]).round(3))
print("各城市金额中位数:")
print(df.groupby("city")["amount"].median())`
  ),
  pt(
    'value-counts',
    '频次统计与去重',
    'value_counts / unique / nunique：类别分布三件套。',
    [SEL('col', '统计列', '品类', ['城市', '品类'])],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
col = {"城市": "city", "品类": "category"}[${JSON.stringify(str(v.col) || '品类')}]
print(f"{col} 频次:")
print(df[col].value_counts())
print(f"\\n去重值: {sorted(df[col].unique())}，共 {df[col].nunique()} 类")
print("占比:")
print((df[col].value_counts(normalize=True) * 100).round(1))`
  ),
  pt(
    'concat-stack',
    '表拼接',
    'concat 纵向堆叠两个月份的订单 + ignore_index 重排索引。',
    [],
    () => `sep = pd.read_csv(io.StringIO(ORDERS_CSV))
oct_part = sep.copy()
oct_part["order_id"] = oct_part["order_id"] + 100
oct_part["order_date"] = oct_part["order_date"].str.replace("09", "10")
both = pd.concat([sep, oct_part], ignore_index=True)
print(f"9 月 {len(sep)} 行 + 10 月 {len(oct_part)} 行 → 合计 {len(both)} 行")
print(both["order_date"].str[:3].value_counts())`
  ),
  pt(
    'melt',
    '宽表转长表',
    'melt 把「城市×月份」宽表融为长表——画图与聚合的前置变形。',
    [],
    () => `wide = pd.DataFrame({
    "city": ["北京", "上海", "广州"],
    "9月": [1200, 1580, 990],
    "10月": [1310, 1495, 1120],
})
print("宽表:")
print(wide)
long = wide.melt(id_vars="city", var_name="month", value_name="amount")
print("\\n长表:")
print(long)`
  ),
  pt(
    'export',
    '导出 CSV 与 JSON',
    '清洗结果落盘：to_csv / to_json 双格式产物（运行目录可见）。',
    [],
    () => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
df["amount"] = df["amount"] * 1.0
df.to_csv("orders_clean.csv", index=False, encoding="utf-8")
df.to_json("orders_clean.json", orient="records", force_ascii=False, indent=2)
back = pd.read_csv("orders_clean.csv")
print(f"CSV 回读 {len(back)} 行与源一致: {back.equals(df)}")
import os
print("产物:", [f for f in sorted(os.listdir('.')) if f.startswith('orders_clean')])`
  ),
  pt(
    'plot',
    'DataFrame 快速绘图',
    'df.plot 一行出图：双城气温曲线落盘 chart.png。',
    [],
    () => `import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ax = None
for city, color in (("北京", "#d62728"), ("上海", "#1f77b4")):
    sub = WEATHER[WEATHER["city"] == city]
    ax = sub.plot(x="date", y="temp", figsize=(9, 4), label=city, color=color, ax=ax)
ax.set_title("60 天气温走势")
ax.figure.tight_layout()
ax.figure.savefig("chart.png", dpi=110)
print("已输出 chart.png")
print(WEATHER.groupby("city")["temp"].agg(["mean", "max"]).round(1))`
  ),
  pt(
    'rolling',
    '移窗与扩展统计',
    'rolling / expanding：滑动均值与累计统计的时间序列视角。',
    [N('window', '窗口天数', 7)],
    (v) => `w = WEATHER[WEATHER["city"] == "上海"].copy()
window = ${int(v.window, 7, 2, 30)}
w["temp_ma"] = w["temp"].rolling(window).mean().round(2)
w["cum_max"] = w["temp"].cummax()
print(w[["date", "temp", "temp_ma", "cum_max"]].tail(8))
print(f"\\n窗口={window} 的移窗均值平滑了日内波动（前 {window - 1} 行为 NaN 属正常）")`
  ),
  pt(
    'cut-bins',
    '分箱 cut/qcut',
    '连续值离散化：等宽 cut 与等频 qcut 的分桶对比。',
    [N('bins', '分箱数', 3)],
    (v) => `df = pd.read_csv(io.StringIO(STUDENTS_CSV))
df["total"] = df[["chinese", "math", "english"]].fillna(0).sum(axis=1)
bins = ${int(v.bins, 3, 2, 5)}
df["等宽档"] = pd.cut(df["total"], bins=bins, labels=[f"档{i + 1}" for i in range(bins)])
df["等频档"] = pd.qcut(df["total"], q=bins, labels=[f"Q{i + 1}" for i in range(bins)])
print(df[["name", "total", "等宽档", "等频档"]])
print("\\n等宽分箱计数:")
print(df["等宽档"].value_counts().sort_index())`
  ),
  pt(
    'method-chain',
    '方法链风格',
    'query/sort_values/head 链式管道：一段代码完成「筛-排-取」。',
    [N('amount', '金额下限', 150)],
    (v) => `df = pd.read_csv(io.StringIO(ORDERS_CSV))
amount = ${int(v.amount, 150, 50, 1000)}
result = (
    df.query("amount >= @amount")
      .assign(金额权重=lambda d: d["amount"] * d["qty"])
      .sort_values("金额权重", ascending=False)
      .loc[:, ["order_id", "city", "category", "金额权重"]]
      .head(5)
)
print(f"金额≥{amount} 的订单按权重 Top5:")
print(result)`
  )
]

// ---------------------------------------------------------------------------
// 数据分析实验室：20 类型归并单页（与 games-lab 同构）
// ---------------------------------------------------------------------------
const PANDAS_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '分析类型',
  type: 'select',
  default: 'read-csv',
  width: 'full',
  options: PANDAS_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const pandasLabSchema: InteractiveToolSchema = {
  id: 'interactive:pandas-lab',
  title: '数据分析实验室',
  description:
    'pandas 全链路 20 个类型：读取/筛选/聚合/透视/连接/清洗/时间/导出/绘图，内置演示数据离线可跑，参数即改即得。',
  tags: ['数据分析', 'pandas'],
  fields: (v) => {
    const t = PANDAS_TYPES.find((x) => x.value === v.type) ?? PANDAS_TYPES[0]!
    return [PANDAS_TYPE_FIELD, ...(t.fields ?? [])]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '类型', value: String(v.type ?? 'read-csv') }] }),
  headerFor: (v) => {
    const t = PANDAS_TYPES.find((x) => x.value === v.type) ?? PANDAS_TYPES[0]!
    return { title: t.label, description: t.description }
  },
  pyCode: (v) => {
    const t = PANDAS_TYPES.find((x) => x.value === v.type) ?? PANDAS_TYPES[0]!
    return `${PANDAS_HEAD}\n# ---- 类型：${t.label} ----\n${t.body(v)}\n`
  }
}
