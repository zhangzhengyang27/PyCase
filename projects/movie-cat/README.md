# movie-cat

基于 Flask 的在线视频/电影信息展示项目。

## 技术栈

- Flask + Flask-SQLAlchemy
- Flask-DebugToolbar
- Flask-APScheduler / APScheduler（定时任务）
- Tornado（可选部署）
- MySQL
- Bootstrap 3 + jQuery + Layer

## 目录结构

```
movie-cat/
├── application.py        # Flask 应用入口
├── www.py                # 启动脚本
├── manager.py            # 命令行管理脚本
├── tornado_server.py     # Tornado 部署入口
├── config/               # 配置文件
│   ├── base_setting.py   # 基础配置
│   ├── local_setting.py  # 本地开发配置（需自行设置数据库连接）
│   └── production_setting.py  # 生产环境配置
├── common/               # 公共模块
│   ├── libs/             # 工具类
│   └── models/           # SQLAlchemy 模型
├── controllers/          # 视图控制器
├── interceptors/         # 拦截器（登录校验、错误处理）
├── jobs/                 # 定时任务
├── static/               # 静态资源
├── templates/            # Jinja2 模板
└── test/                 # 测试脚本
```

## 运行方式

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 创建 MySQL 数据库 `movie_cat`。

3. 设置环境变量或修改 `config/local_setting.py`：

```bash
export MOVIE_CAT_DATABASE_URI="mysql://root:YOUR_PASSWORD@127.0.0.1/movie_cat"
export MOVIE_CAT_SECRET_KEY="your-secret-key"
```

4. 启动开发服务器：

```bash
python www.py
```

## 说明

- `config/local_setting.py` 中的数据库密码已脱敏，请替换为自己的配置。
- 定时任务配置在 `jobs/launcher.py` 和 `jobs/tasks/movie.py` 中。
