# -*- coding: utf-8 -*-


import os
# 本地开发环境配置文件
from config.base_setting import *
# SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "MOVIE_CAT_BACKUP_DATABASE_URI",
    "mysql://root:YOUR_PASSWORD@127.0.0.1/movie_cat"
)

SECRET_KEY = os.environ.get("MOVIE_CAT_BACKUP_SECRET_KEY", "YOUR_SECRET_KEY")


DOMAIN = {
    "www":"http://127.0.0.1:5000"
}


# RELEASE_PATH = "/home/www/release_version"

RELEASE_VERSION = "201907200910"  # 版本号
