"""YAML ↔ JSON：python xxx.py yaml2json config.yaml"""
import argparse
import json
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["yaml2json", "json2yaml"])
    ap.add_argument("file")
    args = ap.parse_args()
    src = Path(args.file)
    if args.mode == "yaml2json":
        data = yaml.safe_load(src.read_text(encoding="utf-8"))
        out = src.with_suffix(".json")
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        data = json.loads(src.read_text(encoding="utf-8"))
        out = src.with_suffix(".yaml")
        out.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("->", out)


if __name__ == "__main__":
    main()
