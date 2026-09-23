"""分析模块：对爬取的文本（评论/标题）做分词统计与词云可视化。

借鉴此前被删除的 2-10 课程里的可视化能力，但改用合规、仍在维护的
jieba + wordcloud 实现，不依赖任何已关停的第三方库。

依赖为可选安装：
    pip install jieba wordcloud matplotlib

仅做本地文本处理，不发起任何网络请求。
"""

import os
import re
from collections import Counter

# 常见中文停用词（精简版，覆盖 B站 评论高频无意义词）
_STOP_WORDS = set(
    "的 了 是 在 我 你 他 她 它 们 这 那 有 和 就 不 也 都 而 及 与 或 把 被 "
    "啊 吧 呢 吗 哦 嗯 哈 啦 嘛 着 过 又 还 很 太 个 没 没 让 给 但 却 等 就 要 "
    "这个 那个 什么 怎么 为什么 因为 所以 如果 已经 可以 应该 感觉 真的 觉得 "
    "视频  UP 主 还是 这样 那样 已经 现在 一个 一直 自己 他们 我们 你们".split()
)


def _load_jieba():
    """惰性导入 jieba，缺失时抛出友好异常。"""
    try:
        import jieba
        return jieba
    except ImportError as e:
        raise RuntimeError(
            "未安装 jieba，无法分词。请先执行: pip install jieba wordcloud matplotlib"
        ) from e


def _load_wordcloud():
    """惰性导入 wordcloud/matplotlib，缺失时抛出友好异常。"""
    try:
        from wordcloud import WordCloud
        import matplotlib

        matplotlib.use("Agg")  # 无 GUI 环境也能保存图片
        import matplotlib.pyplot as plt
        return WordCloud, plt
    except ImportError as e:
        raise RuntimeError(
            "未安装 wordcloud/matplotlib，无法生成词云。请先执行: "
            "pip install jieba wordcloud matplotlib"
        ) from e


def tokenize(texts, top_k=50):
    """对文本列表分词并统计词频，返回 [(词, 次数), ...] 降序列表。

    :param texts: 字符串列表（评论内容或标题）
    :param top_k: 返回前 K 个高频词
    """
    jieba = _load_jieba()
    counter = Counter()
    for text in texts:
        if not text:
            continue
        # 去除 URL 与表情符号等非中英文数字字符干扰
        cleaned = re.sub(r"http\S+|[^\u4e00-\u9fa5A-Za-z0-9]", " ", str(text))
        for word in jieba.cut(cleaned):
            word = word.strip()
            if len(word) < 2:  # 过滤单字
                continue
            if word in _STOP_WORDS:
                continue
            counter[word] += 1
    return counter.most_common(top_k)


def _default_cjk_font():
    """按平台返回常见中文字体路径，找不到则返回 None。"""
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",                              # macOS
        "/System/Library/Fonts/STHeiti Medium.ttc",                        # macOS 旧版
        "C:/Windows/Fonts/msyh.ttc",                                       # Windows 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",                                     # Windows 黑体
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",          # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",                  # Linux 文泉驿
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def generate_wordcloud(texts, output_path="output/wordcloud.png", top_k=200, font_path=None):
    """生成词云图片并保存，返回图片路径；无数据则返回 None。"""
    words = tokenize(texts, top_k=top_k)
    if not words:
        print("没有足够的文本生成词云")
        return None

    WordCloud, plt = _load_wordcloud()
    if font_path is None:
        font_path = _default_cjk_font()
        if font_path is None:
            print("警告：未找到系统中文字体，词云中的中文可能显示为方框")

    # 按词频生成：内置字体不含 CJK 字形，必须指定中文字体
    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=600,
        background_color="white",
        max_words=top_k,
    )
    wc.generate_from_frequencies(dict(words))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wc.to_file(output_path)

    # 同时保存一份词频 CSV，便于后续分析
    csv_path = os.path.splitext(output_path)[0] + "_words.csv"
    import csv

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["词语", "频次"])
        writer.writerows(words)

    print(f"词云已保存: {output_path}")
    print(f"词频表已保存: {csv_path}")
    return output_path


def summarize_texts(texts, top_k=20):
    """对文本列表做基础统计并打印摘要，返回高频词列表（供脚本直接复用）。"""
    words = tokenize(texts, top_k=top_k)
    total = sum(c for _, c in words)
    print(f"\n分析文本 {len(texts)} 条，提取有效词 {total} 个，Top {len(words)} 高频词：")
    for i, (word, count) in enumerate(words, 1):
        print(f"{i:>2}. {word:<10} {count}")
    return words


if __name__ == "__main__":
    # 演示：直接读取 output 下任意评论 CSV，做词云与统计
    import glob
    import csv

    files = glob.glob("output/*评论*.csv") + glob.glob("output/B站评论*.csv")
    if not files:
        print("未找到评论 CSV（请先运行评论爬虫导出 CSV），使用内置示例文本演示。")
        sample = [
            "这个视频真的太好看了，UP主加油",
            "内容很干货，学到了很多，感谢分享",
            "画质清晰，剪辑也很流畅，期待下一期",
            "太喜欢这个系列了，已经三连支持",
        ]
        texts = sample
    else:
        texts = []
        with open(files[0], encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                texts.append(row.get("评论内容", ""))
        print(f"已加载评论文件: {files[0]}，共 {len(texts)} 条")

    summarize_texts(texts)
    try:
        generate_wordcloud(texts)
    except RuntimeError as e:
        print(e)
