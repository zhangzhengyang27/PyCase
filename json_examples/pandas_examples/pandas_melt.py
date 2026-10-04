"""（数据分析实验室生成脚本：内置演示数据，离线可跑）"""
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

WEATHER = None  # 由 rng 生成：60 天 × 北京/上海 的温度湿度
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

# ---- 类型：宽表转长表 ----
wide = pd.DataFrame({
    "city": ["北京", "上海", "广州"],
    "9月": [1200, 1580, 990],
    "10月": [1310, 1495, 1120],
})
print("宽表:")
print(wide)
long = wide.melt(id_vars="city", var_name="month", value_name="amount")
print("\n长表:")
print(long)
