# Vega 新闻管理系统

基于命令行的新闻管理系统，支持角色权限控制（管理员/新闻编辑），提供新闻审批、删除及用户 CRUD 操作。

## 文件结构

- `app.py` — 主程序入口，命令行交互菜单与业务逻辑
- `service/news_service.py` — 新闻服务层：审批、删除、分页查询
- `service/role_service.py` — 角色服务层：角色列表查询
- `service/user_service.py` — 用户服务层：登录验证、增删改查
- `vega/` — 数据访问层（DAO）：`vega/db/` 含 MySQL 连接池与各表 DAO
- `test.py` — colorama 彩色输出测试
- `requirements.txt` — 项目依赖清单

## 核心功能

- 用户登录与角色鉴权（管理员/新闻编辑）
- 管理员：审批新闻、删除新闻、添加/修改/删除用户
- 新闻编辑：菜单暂为占位（提示功能开发中并退出登录）
- 分页浏览，支持上/下一页导航

## 安装依赖并运行

1. 安装 Python 依赖（colorama 终端彩色输出、mysql-connector-python 数据库驱动）：

```bash
pip install -r requirements.txt
```

2. 准备 MySQL 数据库：按实际环境修改 `vega/db/mysql_db.py` 中的连接配置
   （默认 `localhost:3306`，用户 `root`，数据库 `vega`），并确保库中已建好
   `t_user` / `t_role` / `t_news` / `t_type` 等表（建表脚本见课程第09周资料）。

3. 在项目目录下运行：

```bash
python app.py
```
