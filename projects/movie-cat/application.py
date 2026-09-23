# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import pymysql

# 使用 pymysql 代替 MySQLdb 驱动，避免 "No module named 'MySQLdb'" 报错
pymysql.install_as_MySQLdb()

app = Flask( __name__ )

app.config.from_pyfile( "config/base_setting.py" )
#ops_config=local|production
#linux export ops_config=local|production
#windows set ops_config=local|production
ops_config = os.environ.get( "ops_config", "local" )
app.config.from_pyfile( "config/%s_setting.py"%( ops_config ) )

db = SQLAlchemy( app )



