"""记账本：add <分类> <金额> [备注] | report [月份]"""
import argparse
import sqlite3
from collections import defaultdict

DB = "expenses.db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["add", "report"])
    ap.add_argument("args", nargs="*")
    args = ap.parse_args()
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS expenses (date TEXT, category TEXT, amount REAL, note TEXT)")
    if args.cmd == "add" and len(args.args) >= 2:
        from datetime import date
        cat, amount = args.args[0], float(args.args[1])
        note = args.args[2] if len(args.args) > 2 else ""
        conn.execute("INSERT INTO expenses VALUES (?, ?, ?, ?)", (date.today().isoformat(), cat, amount, note))
        conn.commit()
        print(f"已记: {cat} ¥{amount}")
    else:
        month = args.args[0] if args.args else __import__("datetime").date.today().strftime("%Y-%m")
        by_cat = defaultdict(float)
        for cat, amount in conn.execute("SELECT category, amount FROM expenses WHERE date LIKE ?", (month + "%",)):
            by_cat[cat] += amount
        total = sum(by_cat.values())
        for cat in sorted(by_cat, key=by_cat.get, reverse=True):
            print(f"{cat:<10} ¥{by_cat[cat]:>8.2f}  {'█' * int(by_cat[cat] / max(total, 1) * 20)}")
        print(f"{'合计':<10} ¥{total:>8.2f}")
    conn.close()


if __name__ == "__main__":
    main()
