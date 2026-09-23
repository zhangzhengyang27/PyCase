# -*- coding: utf-8 -*-
from application import app
from .DataHelper import getCurrentTime
import os


class UrlManager(object):
    @staticmethod
    def buildUrl(path):
        config_domain = app.config['DOMAIN']  # 从配置文件中获取域名
        return "%s%s" % (config_domain['www'], path)  # 拼接域名

    @staticmethod
    def buildStaticUrl(path):
        path = "/static" + path + "?ver=" + UrlManager.getReleaseVersion()  # 版本管理
        return UrlManager.buildUrl(path)

    @staticmethod
    def getReleaseVersion():
        """
        版本管理
        开发模式 使用时间作为版本号
        生产环境 使用版本文件进行管理，覆盖开发模式的值
        :return:
        """
        ver = "%s" % (getCurrentTime("%Y%m%d%H%M%S%f")) # 获取当前时间作为版本号
        release_path = app.config.get('RELEASE_PATH') # 从配置文件中获取版本文件路径
        if release_path and os.path.exists(release_path):
            with open(release_path, 'r') as f:
                ver = f.readline()
        return ver
