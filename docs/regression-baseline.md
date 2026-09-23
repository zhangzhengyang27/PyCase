# 示例抽样回归报告

- 生成时间：2026-09-09 21:53:07
- 抽样比例：0.1（seed=42），试跑 120 个
- 解释器：/Users/xiaoye/Desktop/20260803/Python/desktop-app/.venv/bin/python

| 状态 | 数量 | 占比 |
|---|---|---|
| pass | 80 | 66.7% |
| missing_dependency | 9 | 7.5% |
| timeout | 8 | 6.7% |
| failed | 23 | 19.2% |

## 非通过样本（前 30 条）

| 示例 | 分类 | 状态 | 耗时(s) | 原因 |
|---|---|---|---|---|
| word2.py | topics | failed | 0.08 | docx.opc.exceptions.PackageNotFoundError: Package not found at './resources/用函数还 |
| 15.py | topics | failed | 3.29 | requests.exceptions.SSLError: HTTPSConnectionPool(host='www.doutupk.com', port=4 |
| main.py | projects | missing_dependency | 4.04 | ModuleNotFoundError: No module named 'valley.code' |
| 04-sqlalchemy-two-table-relation.py | topics | failed | 1.97 | (Background on this error at: https://sqlalche.me/e/20/e3q8) |
| 2-demo.py | topics | timeout | 8.0 | 超过 8.0s 未退出 |
| task-1001.py | topics | failed | 0.83 | KeyError: 'words_result' |
| 07-sqlalchemy-data-response.py | topics | failed | 0.24 | (Background on this error at: https://sqlalche.me/e/20/e3q8) |
| manager.py | projects | missing_dependency | 0.09 | ModuleNotFoundError: No module named 'flask._compat' |
| example10.py | topics | timeout | 8.01 | 超过 8.0s 未退出 |
| house-scene.py | topics | timeout | 8.03 | 超过 8.0s 未退出 |
| favorite.py | topics | failed | 0.15 | FileNotFoundError: [Errno 2] No such file or directory: '/Users/xiaoye/Desktop/2 |
| 05-test-functions.py | topics | failed | 0.38 | AttributeError: module 'psutil' has no attribute 'test' |
| LoginPage.py | topics | missing_dependency | 0.04 | ModuleNotFoundError: No module named 'autotest' |
| 14-douban-movie-crawler.py | topics | failed | 0.71 | requests.exceptions.ProxyError: HTTPSConnectionPool(host='movie.douban.com', por |
| task-0401.py | topics | failed | 1.94 | requests.exceptions.SSLError: HTTPSConnectionPool(host='dytt.dytt8.net', port=44 |
| baidu-ocr.py | topics | missing_dependency | 0.1 | ModuleNotFoundError: No module named 'utils.base_tool' |
| user.py | topics | failed | 0.11 | FileNotFoundError: [Errno 2] No such file or directory: '/Users/xiaoye/Desktop/2 |
| l-system-plant.py | topics | timeout | 8.01 | 超过 8.0s 未退出 |
| demo6.py | topics | failed | 0.12 | TypeError: WebDriver.__init__() got an unexpected keyword argument 'executable_p |
| game.py | topics | failed | 0.03 | EOFError: EOF when reading a line |
| 08-regex-movie-crawler-advanced.py | topics | failed | 1.17 | requests.exceptions.SSLError: HTTPSConnectionPool(host='dytt.dytt8.net', port=44 |
| orbit-flowers.py | topics | timeout | 8.01 | 超过 8.0s 未退出 |
| task-0303.py | topics | failed | 1.01 | requests.exceptions.ProxyError: HTTPSConnectionPool(host='www.cheshi.com', port= |
| app.py | topics | missing_dependency | 0.15 | ImportError: attempted relative import with no known parent package |
| renju.py | topics | timeout | 8.0 | 超过 8.0s 未退出 |
| jingdong.py | topics | missing_dependency | 0.2 | ImportError: attempted relative import with no known parent package |
| requests-html.py | topics | missing_dependency | 0.77 | Install lxml[html-clean] or lxml_html_clean directly. |
| triangle.py | topics | failed | 0.04 | EOFError: EOF when reading a line |
| object-parent-child.py | topics | failed | 0.03 | AttributeError: 'Parent' object has no attribute 'play_pingpong' |
| demo13.py | topics | failed | 0.1 | TypeError: WebDriver.__init__() got an unexpected keyword argument 'executable_p |
