"""CSV ↔ JSON：python xxx.py csv2json data.csv / json2csv data.json"""
import argparse
import csv
import json
from pathlib import Path


def typed(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["csv2json", "json2csv"])
    ap.add_argument("file")
    args = ap.parse_args()
    src = Path(args.file)

    if args.mode == "csv2json":
        rows = list(csv.DictReader(src.open(encoding="utf-8")))
        rows = [{k: typed(v) for k, v in r.items()} for r in rows]
        out = src.with_suffix(".json")
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {out}（{len(rows)} 行）")
    else:
        rows = json.loads(src.read_text(encoding="utf-8"))
        out = src.with_suffix(".csv")
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"-> {out}（{len(rows)} 行）")


if __name__ == "__main__":
    main()
