# Flask 问答社区

基于 Flask 的问答社区前端项目，包含首页、登录注册、文章编写、个人中心等页面。

## 文件结构

- `app.py` — Flask 应用入口，定义路由（首页/关注/登录/注册/写文章/个人中心/问题详情）
- `templates/` — Jinja2 模板（base.html、index.html、login.html、register.html、write.html、mine.html、detail.html 等）
- `assets/` — 静态资源（CSS 样式、JS 脚本、Bootstrap 插件、图片素材）

## 核心功能

- 首页展示与关注页
- 用户登录与注册
- 写文章/提问
- 个人中心与问题详情

## 运行方式

```bash
python app.py
```

## 依赖

- Flask（根目录 requirements.txt 已包含）
- 前端使用 Bootstrap 3 + jQuery 3.4.1，无需额外安装
