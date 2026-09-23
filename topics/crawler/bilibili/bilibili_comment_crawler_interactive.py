import time
import random
import re

from bili_api import safe_request_json
from utils.link_parser import parse_bvid
from utils.exporter import export_records


def get_video_info(video_id):
    """获取视频信息，主要是获取 aid 与标题（请求由 bili_api 统一处理）。

    :param video_id: BV 号（如 BV13SR5YMEis）或 av 号（如 av170001）
    """
    url = "https://api.bilibili.com/x/web-interface/view"
    if video_id[:2].lower() == "av":
        params = {"aid": video_id[2:]}  # view 接口不认 av 字符串，需传 aid 数字
    else:
        params = {"bvid": video_id}
    data = safe_request_json(url, params=params)
    if data is None:
        return None, None
    video = data.get("data") or {}
    return video.get("aid"), video.get("title")


def get_comments(aid, page=1, page_size=20):
    """获取视频单页评论（请求由 bili_api 统一处理）。"""
    if not aid:
        print("aid 为空，无法获取评论")
        return None
    url = "https://api.bilibili.com/x/v2/reply"
    params = {
        "type": 1,  # 评论类型，1表示视频评论
        "oid": aid,
        "pn": page,
        "ps": page_size,
        "sort": 2,  # 排序方式，2表示按热度排序
    }
    data = safe_request_json(url, params=params)
    return data.get("data") if data else None


def extract_bvid(url):
    """从输入中提取 BV 号（兼容完整链接 / 纯 BV 号 / av 号）。"""
    return parse_bvid(url)


def save_comments_to_txt(comments, title, formats=("txt", "csv", "json")):
    """将评论导出为多格式文件（默认 TXT/CSV/JSON），按标题生成文件名后缀。"""
    records = []
    for i, comment in enumerate(comments, 1):
        member = comment.get("member") or {}
        content = comment.get("content") or {}
        records.append({
            "序号": i,
            "用户": member.get("uname", "未知用户"),
            "性别": member.get("sex", "未知"),
            "等级": member.get("level_info", {}).get("current_level", 0),
            "IP属地": (comment.get("reply_control") or {}).get("location", "未知"),
            "时间": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(comment.get("ctime", 0))
            ),
            "点赞": comment.get("like", 0),
            "评论内容": content.get("message", ""),
        })

    suffix = re.sub(r'[\\/*?:"<>|]', "_", title)[:20] if title else ""
    paths = export_records(
        records, "B站评论", formats=formats, suffix=suffix, title=f"视频标题: {title}"
    )
    return paths


def main():
    print("=" * 50)
