"""关联抓取：帖子与其评论的聚合。"""
import requests

posts = requests.get("https://jsonplaceholder.typicode.com/posts",
                     params={"_limit": 3}, timeout=10).json()
for post in posts:
    comments = requests.get(
        f"https://jsonplaceholder.typicode.com/posts/{post['id']}/comments",
        timeout=10).json()
    print(f"[{post['id']}] {post['title'][:20]}… 评论 {len(comments)} 条")
