# -*- coding: utf-8 -*-
#本地开发环境配置文件
import os
from config.base_setting import *
#SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "MOVIE_CAT_DATABASE_URI",
    "mysql://root:YOUR_PASSWORD@127.0.0.1/movie_cat"
)

SECRET_KEY = os.environ.get("MOVIE_CAT_SECRET_KEY", "YOUR_SECRET_KEY")


DOMAIN = {
    "www":"http://127.0.0.1"
}


#RELEASE_PATH = "/home/www/release_version"
