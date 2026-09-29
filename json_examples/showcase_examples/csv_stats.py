"""CSV 数值列统计：纯标准库实现。"""
import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile", nargs="?", default="demo.csv")
    args = parser.parse_args()

    path = Path(args.csvfile)
    if not path.exists():
        path.write_text(
            "name,score,age\n小明,92,14\n小红,88,13\n小刚,95,15\n小丽,79,14\n",
            encoding="utf-8",
        )

    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("空表格")
        return

    print(f"行数: {len(rows)}，列: {list(rows[0])}")
    for col in rows[0]:
        values = []
        for r in rows:
            try:
                values.append(float(r[col]))
            except ValueError:
                break
        if len(values) == len(rows):
            print(f"  [{col}] 计数={len(values)} 均值={sum(values)/len(values):.2f} "
                  f"最小={min(values)} 最大={max(values)}")


if __name__ == "__main__":
    main()
