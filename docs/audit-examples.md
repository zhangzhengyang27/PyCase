# 示例库健康审计报告（v0.7 修复后）

> 由 `scripts/audit_examples.py` 生成。首轮审计（213 条记录/224 示例）后已执行修复：
> 下架空壳 `__init__.py` 145 个、合并重复 17 个、dir 上调 55 个；误删的 4 个含码
> `__init__.py` 已恢复。当前总量 **1187 个示例**。

## 修复后残留（35 条，均为预期保留项）

### 空壳代码（11 条）
> 非 __init__ 的 docstring-only 文件（不在本轮下架范围，见遗留建议）

- test01.py (migrated.json#328) (22 字符)
- test02.py (migrated.json#329) (25 字符)
- example01.py (migrated.json#331) (21 字符)
- example02.py (migrated.json#332) (25 字符)
- pip-image.py (migrated.json#412) (452 字符)
- pdf1.py (migrated.json#490) (57 字符)
- word1.py (migrated.json#493) (58 字符)
- pip3-image.py (migrated.json#621) (340 字符)
- 2-name.py (migrated.json#674) (11 字符)
- task-02.py (migrated.json#916) (97 字符)
- settings.py (migrated.json#974) (10 字符)

### 依赖缺失（7 条）
> 真缺 pip 包/本地模块（aircv、ddddocr、jenkins、C01 等），需按需安装

- C01 ← 1 个示例，如 task-0102.py (migrated.json#54)
- C1104 ← 1 个示例，如 task-1105.py (migrated.json#68)
- TencentYoutuyun ← 1 个示例，如 image_recognition_zhihu.py (migrated.json#1012)
- autotest ← 3 个示例，如 LoginPage.py (migrated.json#25)
- corner_widget ← 2 个示例，如 window.py (migrated.json#137)
- example ← 1 个示例，如 game.py (migrated.json#142)
- pydocx ← 1 个示例，如 05-docx-to-pdf.py (migrated.json#289)

### 安全高危（17 条）
> 应用分级设计内（隔离运行 + 白名单），UI 已加高危徽章提示运行前审阅代码（子进程运行 + 环境变量白名单，非沙箱）

- process-redis.py (migrated.json#17)：文件或目录删除操作
- login.py (migrated.json#46)：系统命令执行：system()
- splinter-use.py (migrated.json#56)：文件或目录删除操作
- 2-exception-handling.py (migrated.json#114)：文件或目录删除操作
- example-10.py (migrated.json#115)：文件或目录删除操作
- example-8.py (migrated.json#121)：文件或目录删除操作
- backup.py (migrated.json#242)：系统命令执行：popen()
- backup.py (migrated.json#251)：系统命令执行：popen()
- function4.py (migrated.json#442)：系统命令执行：system()
- clock.py (migrated.json#483)：系统命令执行：system()
- marquee.py (migrated.json#539)：系统命令执行：system()
- tic-tac-toe.py (migrated.json#543)：系统命令执行：system()
- … 另 5 条
