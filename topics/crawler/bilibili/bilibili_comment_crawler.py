import time
import random

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
    """从URL中提取BV号（兼容完整链接/纯 BV 号/av 号）。"""
    return parse_bvid(url)


def save_comments_to_txt(comments, title, formats=("txt", "csv", "json")):
    """将评论导出为多格式文件（默认 TXT/CSV/JSON）。

    :param comments: 评论列表（B站 原始结构）
    :param title: 视频标题，用于文件名后缀
    :param formats: 导出格式元组
    :return: 生成的文件路径列表
    """
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

    suffix = title[:20] if title else ""
    paths = export_records(
        records, "B站评论", formats=formats, suffix=suffix, title=f"视频标题: {title}"
    )
    for p in paths:
        print(f"评论已保存到 {p}")
    return paths


def main():
    # 视频URL（支持完整链接 / 纯 BV 号 / av 号）
    # 分享链接里的 spm_id_from / vd_source 是用户级跟踪参数，保留会泄露来源
    video_url = "https://www.bilibili.com/video/BV13SR5YMEis/"

    # 提取BV号
    bvid = extract_bvid(video_url)
    if not bvid:
        print("无法从输入中提取 BV 号")
        return

    print(f"提取到标识: {bvid}")

    # 获取视频信息
    aid, title = get_video_info(bvid)
    if not aid:
        return

    print(f"视频标题: {title}")
    print(f"AID: {aid}")

    # 获取评论
    all_comments = []

    # 首先获取第一页，包含置顶和热门评论
    print("正在获取第 1 页评论...")
    data = get_comments(aid, 1)

    if not data:
        print("获取评论失败")
        return

    # 添加置顶评论
    if data.get("top_replies"):
        print(f"获取到 {len(data['top_replies'])} 条置顶评论")
        all_comments.extend(data["top_replies"])

    # 添加热门评论
    if data.get("hots"):
        print(f"获取到 {len(data['hots'])} 条热门评论")
        all_comments.extend(data["hots"])

    # 添加普通评论
    if data.get("replies"):
        print(f"获取到 {len(data['replies'])} 条普通评论")
        all_comments.extend(data["replies"])

    # 继续获取更多页的普通评论
    page = 2
    max_pages = 5  # 最多获取5页评论

    while page <= max_pages:
        # 每页请求前先随机延迟（含第 1→2 页之间），避免请求过于频繁
        delay = random.uniform(1, 3)
        print(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)

        print(f"正在获取第 {page} 页评论...")
        data = get_comments(aid, page)

        if not data or not data.get("replies"):
            print("没有更多评论了")
            break

        print(f"获取到 {len(data['replies'])} 条普通评论")
        all_comments.extend(data["replies"])

        # 停止条件：本页返回的评论数小于每页大小，说明已是最后一页
        # 或已达到设定的最大页数上限
        page_size = (data.get("page") or {}).get("size") or len(data["replies"])
        if len(data["replies"]) < page_size or page >= max_pages:
            break

        page += 1

    # 去重，因为热门评论可能在普通评论中重复
    unique_comments = []
    rpid_set = set()

    for comment in all_comments:
        rpid = comment.get("rpid")
        if rpid not in rpid_set:
            rpid_set.add(rpid)
            unique_comments.append(comment)

    print(f"共获取到 {len(unique_comments)} 条不重复评论")

    # 保存评论（实际保存路径由 save_comments_to_txt 打印）
    save_comments_to_txt(unique_comments, title)


if __name__ == "__main__":
    main()
