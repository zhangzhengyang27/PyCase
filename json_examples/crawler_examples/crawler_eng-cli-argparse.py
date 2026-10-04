"""CLI：python crawler_cli.py --pages 3 --keyword 爬虫"""
import argparse


def main():
    parser = argparse.ArgumentParser(description="通用抓取脚本骨架")
    parser.add_argument("--pages", type=int, default=1, help="抓取页数")
    parser.add_argument("--keyword", default="", help="过滤关键词")
    parser.add_argument("--output", default="out.jsonl", help="输出文件")
    args = parser.parse_args()
    print(f"计划抓取 {args.pages} 页，关键词={args.keyword or '无'}，输出={args.output}")
    for p in range(1, args.pages + 1):
        print(f"  第 {p} 页 …（此处接入真实抓取逻辑）")


if __name__ == "__main__":
    main()
