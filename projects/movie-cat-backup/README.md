# movie-cat-backup

`movie-cat` 项目的早期/备份版本，同样基于 Flask 构建。

## 说明

本目录是 `movie-cat` 项目的历史备份版本，结构相对简单，保留了项目早期的实现方式。主要用作版本对比和学习参考。

## 技术栈

- Flask + Flask-SQLAlchemy
- Flask-DebugToolbar
- MySQL
- Bootstrap 3 + jQuery + Layer

## 目录结构

```
movie-cat-backup/
├── application.py        # Flask 应用入口
├── www.py                # 启动脚本
├── manager.py            # 命令行管理脚本
├── config/               # 配置文件
│   ├── base_setting.py
│   ├── local_setting.py  # 本地开发配置（需自行设置数据库连接）
│   └── production_setting.py
├── common/               # 公共模块
│   ├── libs/             # 工具类
│   └── models/           # SQLAlchemy 模型
├── controllers/          # 视图控制器
├── interceptors/         # 拦截器
├── static/               # 静态资源
└── templates/            # Jinja2 模板
```

## 运行方式

1. 安装依赖：

```bash
pip install -r requirement.txt
```

2. 创建 MySQL 数据库 `movie_cat`。

3. 设置环境变量或修改 `config/local_setting.py`：

```bash
export MOVIE_CAT_BACKUP_DATABASE_URI="mysql://root:YOUR_PASSWORD@127.0.0.1/movie_cat"
export MOVIE_CAT_BACKUP_SECRET_KEY="your-secret-key"
```

4. 启动开发服务器：

```bash
python www.py
```
