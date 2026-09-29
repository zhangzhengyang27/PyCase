"""GitHub API：抓取 Python 仓库 star 排行（免认证 60 次/小时）。"""
import requests

headers = {"Accept": "application/vnd.github+json"}
resp = requests.get("https://api.github.com/search/repositories",
                    params={"q": "language:python", "sort": "stars", "per_page": 5},
                    headers=headers, timeout=15)
print("剩余配额:", resp.headers.get("X-RateLimit-Remaining"))
for repo in resp.json().get("items", []):
    print(f"{repo['stargazers_count']:>7}  {repo['full_name']}")
