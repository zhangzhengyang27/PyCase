"""链接/ID 自动解析：识别 BV号、AV号、CV号(专栏)、UID(用户)、完整网址。

借鉴 Yi-luo-hua/BilibiliCrawler 的 helpers 思路，让用户无需手动选择类型，
输入任意一种标识都能自动路由到正确的爬取目标。
"""

import re

_BV_RE = re.compile(r"BV[0-9A-Za-z]+")
_AV_RE = re.compile(r"av(\d+)", re.IGNORECASE)
_CV_RE = re.compile(r"cv(\d+)", re.IGNORECASE)
_UID_RE = re.compile(r"(\d{5,})")


class LinkType:
    VIDEO = "video"      # 视频（BV/AV）
    ARTICLE = "article"  # 专栏（CV）
    USER = "user"        # 用户（UID）


def parse(input_str):
    """解析用户输入，返回 (类型, 标识) 二元组；无法识别时返回 (None, None)。

    :param input_str: 可能是 BV号 / av号 / CV号 / UID / 完整网址 / 纯文本标识
    """
    text = (input_str or "").strip()
    if not text:
        return (None, None)

    # 1. 视频：优先匹配 BV 号（出现在网址或纯文本中）
    m = _BV_RE.search(text)
    if m:
        return (LinkType.VIDEO, m.group(0))

    # 2. 视频：av 号
    m = _AV_RE.search(text)
    if m:
        return (LinkType.VIDEO, f"av{m.group(1)}")

    # 3. 专栏：cv 号
    m = _CV_RE.search(text)
    if m:
        return (LinkType.ARTICLE, f"cv{m.group(1)}")

    # 4. 用户：长数字 UID（放在最后，避免误吞 av/cv 后数字）
    m = _UID_RE.search(text)
    if m:
        return (LinkType.USER, m.group(1))

    return (None, None)


def parse_bvid(input_str):
    """针对视频场景的便捷封装：仅当识别为视频时返回 BV/av 标识，否则 None。"""
    link_type, value = parse(input_str)
    if link_type == LinkType.VIDEO:
        return value
    return None
