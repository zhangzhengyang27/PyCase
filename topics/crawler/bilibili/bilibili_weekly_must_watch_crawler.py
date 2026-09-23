import time
import random
import re
from datetime import datetime

from bili_api import safe_request_json
from utils.exporter import export_records


def get_weekly_must_watch_list():
    """获取B站每周必看系列视频列表（请求由 bili_api 统一处理）。"""
    print("=" * 50)
    print("开始搜索B站每周必看系列视频...")
    print("=" * 50)

    search_url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {
        "search_type": "video",
        "keyword": "哔哩哔哩每周必看",
        "order": "pubdate",
        "duration": 0,
        "page": 1,
        "page_size": 50,
    }

    all_videos = []
    max_pages = 20
    total_videos = 0

    # 关键词列表，连续多页无结果时依次切换重试
    keywords = ["哔哩哔哩每周必看", "B站每周必看", "每周必看"]
    keyword_index = 0
    page = 1
    while page <= max_pages:
        params["keyword"] = keywords[keyword_index]
        print(f"\n正在获取第 {page} 页搜索结果（关键词: {params['keyword']}）...")
        params["page"] = page

        data = safe_request_json(search_url, params=params, wbi_sign=True)
        if data is None:
            break

        videos = (data.get("data") or {}).get("result") or []
        if not videos:
            print("该页没有搜索结果，搜索结束")
            break

        print(f"第 {page} 页共获取到 {len(videos)} 个视频")
        total_videos += len(videos)

        # 筛选出官方的每周必看视频
        page_official_videos = 0
        for video in videos:
            title = re.sub(r"<[^>]+>", "", video.get("title", ""))
            author = video.get("author", "")

            print(f"检查视频: {title} - UP主: {author}")

            is_official = False
            if "每周必看" in title:
                if author in [
                    "哔哩哔哩每周必看", "哔哩哔哩", "哔哩哔哩弹幕网",
                    "哔哩哔哩综合", "哔哩哔哩英雄联盟赛事",
                    "哔哩哔哩电影", "哔哩哔哩番剧",
                ]:
                    is_official = True
                elif (
                    "哔哩哔哩每周必看" in title
                    or "B站每周必看" in title
                    or "bilibili每周必看" in title
                ):
                    is_official = True
                elif re.search(r"第\s*\d+\s*期", title):
                    is_official = True

            if is_official:
                print(f"✓ 匹配到官方每周必看视频: {title}")
                page_official_videos += 1
                all_videos.append({
                    "title": title,
                    "bvid": video.get("bvid", ""),
                    "author": author,
                    "pubdate": video.get("pubdate", 0),
                    "duration": video.get("duration", 0),
                    "url": f"https://www.bilibili.com/video/{video.get('bvid', '')}",
                })
            else:
                print("✗ 非官方每周必看视频")

        print(f"第 {page} 页筛选出 {page_official_videos} 个官方每周必看视频")

        if len(all_videos) >= 100:
            print(f"已找到 {len(all_videos)} 个视频，达到目标数量，搜索结束")
            break

        if page_official_videos == 0 and page >= 5:
            if keyword_index < len(keywords) - 1:
                keyword_index += 1
                print(f"连续多页没有找到官方每周必看视频，切换搜索关键词为: {keywords[keyword_index]}")
                page = 1
                continue
            else:
                print("已尝试所有关键词仍未找到，搜索结束")
                break

        delay = random.uniform(1, 2)
        print(f"等待 {delay:.2f} 秒后继续搜索下一页...")
        time.sleep(delay)
        page += 1

    print("\n" + "=" * 50)
    print(f"搜索完成，共搜索 {total_videos} 个视频，筛选出 {len(all_videos)} 个官方每周必看视频")

    if not all_videos:
        print("未找到任何官方每周必看视频，请检查网络 / BILI_COOKIE 是否有效。")
        return []

    # 按发布日期排序（从早到晚）
    all_videos.sort(key=lambda x: x.get("pubdate", 0))

    if all_videos:
        print("\n找到的官方每周必看视频列表:")
        for i, video in enumerate(all_videos, 1):
            print(f"{i}. {video['title']} - {time.strftime('%Y-%m-%d', time.localtime(video.get('pubdate', 0)))}")

    return all_videos


def get_video_details(bvid):
    """获取视频详细信息（请求由 bili_api 统一处理）。"""
    if not bvid:
        return None
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {"bvid": bvid}
    print(f"正在获取视频 {bvid} 的详细信息...")
    data = safe_request_json(url, params=params)
    if data is None:
        return None
    return data.get("data")


def format_number(num):
    """格式化数字，将大数字转换为带单位的形式。"""
    if not isinstance(num, (int, float)):
        return "未知"
    if num >= 100000000:
        return f"{num / 100000000:.2f}亿"
    elif num >= 10000:
        return f"{num / 10000:.2f}万"
    else:
        return str(num)


def extract_episode_number(title):
    """从标题中提取期数。"""
    match = re.search(r"第\s*(\d+)\s*期", title)
    if match:
        return int(match.group(1))
    return 0


def save_to_txt(videos, formats=("txt", "csv", "json")):
    """将每周必看视频信息导出为多格式文件（默认 TXT/CSV/JSON）。

    逐期请求视频详情补全播放/互动数据，构造记录列表后交给统一导出层。
    """
    print("\n" + "=" * 50)
    print(f"开始保存 {len(videos)} 期每周必看视频信息...")
    print("=" * 50)

    records = []
    for i, video in enumerate(videos, 1):
        title = video.get("title", "未知标题")
        bvid = video.get("bvid", "")
        author = video.get("author", "未知UP主")
        episode = extract_episode_number(title)
        publish_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(video.get("pubdate", 0))
        )

        print(f"\n[{i}/{len(videos)}] 正在处理第 {episode if episode > 0 else '未知'} 期视频: {title}")

        video_detail = get_video_details(bvid)
        if video_detail:
            stat = video_detail.get("stat") or {}
            desc = video_detail.get("desc", "无描述")
        else:
            print("获取视频详情失败，使用默认值")
            stat = {}
            desc = "无描述"

        records.append({
            "期数": episode if episode > 0 else "未知",
            "标题": title,
            "BV号": bvid,
            "UP主": author,
            "发布时间": publish_time,
            "播放量": stat.get("view", 0),
            "弹幕数": stat.get("danmaku", 0),
            "点赞数": stat.get("like", 0),
            "投币数": stat.get("coin", 0),
            "收藏数": stat.get("favorite", 0),
            "分享数": stat.get("share", 0),
            "评论数": stat.get("reply", 0),
            "视频链接": video.get("url", ""),
            "简介": desc,
        })

        if i < len(videos):
            print("等待 3 秒后爬取下一期...")
            time.sleep(3)

    paths = export_records(
        records, "B站每周必看系列", formats=formats, title="B站每周必看系列视频"
    )
    print("\n" + "=" * 50)
    for p in paths:
        print(f"视频信息已保存到 {p}")
    print("=" * 50)
    return paths


def main():
    print("\n" + "=" * 50)
    print("B站每周必看系列爬虫")
    print("=" * 50)

    print("\n开始获取B站每周必看系列视频列表...")
    videos = get_weekly_must_watch_list()

    if not videos:
        print("\n未获取到视频数据，爬虫结束")
        return

    print(f"\n成功获取到 {len(videos)} 期每周必看视频")

    print("\n正在按期数排序视频...")
    videos.sort(key=lambda x: extract_episode_number(x.get("title", "")))

    print("\n排序后的视频列表:")
    for i, video in enumerate(videos, 1):
        episode = extract_episode_number(video.get("title", ""))
        print(f"{i}. 第 {episode if episode > 0 else '未知'} 期: {video.get('title', '')}")

    output_files = save_to_txt(videos)
    print(f"\n爬虫任务完成！视频信息已保存到: {', '.join(output_files)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n\n程序出错: {e}")
    finally:
        input("\n按Enter键退出...")
