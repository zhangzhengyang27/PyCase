"""JSON → dataclass：样本推断字段类型。"""
import argparse
import json


def py_type(v):
    if isinstance(v, bool): return "bool"
    if isinstance(v, int): return "int"
    if isinstance(v, float): return "float"
    if isinstance(v, dict): return "dict[str, object]"
    if isinstance(v, list): return "list"
    return "str"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--class-name", default="Item")
    args = ap.parse_args()
    sample = json.loads(__import__("pathlib").Path(args.file).read_text(encoding="utf-8"))
    if isinstance(sample, list) and sample:
        sample = sample[0]
    fields = [f"    {k}: {py_type(v)}" for k, v in sample.items()]
    print(f"@dataclass\nclass {args.class_name}:\n" + "\n".join(fields))


if __name__ == "__main__":
    main()
