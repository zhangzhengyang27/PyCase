"""统一导出层：将结构化记录列表导出为 TXT / CSV / JSON。

各爬虫只需把数据整理成 dict 列表，再调用本模块即可输出多种格式，
避免每个脚本各自实现保存逻辑。CSV / JSON 适合后续数据分析。
"""

import os
import csv
import json
from datetime import datetime

# 输出目录锚定在 bilibili 模块目录下（crawler/bilibili/output），
# 不随运行时 CWD 变化——从仓库根运行脚本时结果仍在模块目录
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"
)

_FORMATS = ("txt", "csv", "json")


def _safe_filename(name):
    """将任意标题清洗为安全的文件名片段。"""
    import re
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def _ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    return OUTPUT_DIR


def _build_path(prefix, ext, suffix=""):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # B站标题常含 / ? : | 等非法文件名字符，必须清洗，否则 open() 直接失败
    safe_prefix = _safe_filename(str(prefix)).strip() or "export"
    safe_suffix = _safe_filename(str(suffix)).strip()[:50] if suffix else ""
    name = f"{safe_prefix}_{timestamp}{('_' + safe_suffix) if safe_suffix else ''}.{ext}"
    return os.path.join(_ensure_output_dir(), name)


def export_records(records, prefix, *, formats=_FORMATS, suffix="", title=None):
    """导出记录列表为指定格式，返回生成的文件路径列表。

    :param records: list[dict]，每条记录为一个字段字典
    :param prefix: 文件名前缀（如 "B站播放量排行榜"）
    :param formats: 导出格式元组，默认全部
    :param suffix: 文件名附加后缀（如视频标题）
    :param title: TXT 顶部标题行（可选）
    :return: 实际成功生成的文件路径列表
    """
    if not records:
        print("没有数据可导出")
        return []

    paths = []
    if "txt" in formats:
        paths.append(_export_txt(records, prefix, suffix, title))
    if "csv" in formats:
        paths.append(_export_csv(records, prefix, suffix))
    if "json" in formats:
        paths.append(_export_json(records, prefix, suffix))
    return [p for p in paths if p]


def _export_txt(records, prefix, suffix, title):
    path = _build_path(prefix, "txt", suffix)
    with open(path, "w", encoding="utf-8") as f:
        if title:
            f.write(title + "\n")
        f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"共 {len(records)} 条记录\n")
        f.write("=" * 50 + "\n\n")
        for i, rec in enumerate(records, 1):
            f.write(f"#{i}\n")
            for key, value in rec.items():
                f.write(f"{key}: {value}\n")
            f.write("-" * 50 + "\n\n")
    return path


def _export_csv(records, prefix, suffix):
    path = _build_path(prefix, "csv", suffix)
    # 以所有记录出现过的字段并集作为表头，保证列完整
    fields = []
    for rec in records:
        for k in rec:
            if k not in fields:
                fields.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)
    return path


def _export_json(records, prefix, suffix):
    path = _build_path(prefix, "json", suffix)
    payload = {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(records),
        "records": records,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path
