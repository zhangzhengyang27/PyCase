# -*- coding: utf-8 -*-
from application import app, db
import requests, os, time, hashlib, json, re
from bs4 import BeautifulSoup
from common.libs.DataHelper import getCurrentTime
from urllib.parse import urlparse
from common.models.movie import Movie

'''
python manager.py runjob -m movie -a list | parse
'''


class JobTask():
    def __init__(self):
        self.source = "btbtdy"
        self.url = {
            "num": 3,  # 获取列表页数
            "url": "http://www.btbtdy.me/btfl/dy1-#d#.html",
            # 处理分页：http://www.btbtdy.me/btfl/dy1.html、http://www.btbtdy.me/btfl/dy1-2.html
            "path": "/tmp/%s/" % (self.source)  # 保存路径
        }

    # 第一步 首先获取列表 list html 回来，通过解析 html 获取详情的 url 等信息，在根据详情 url 获取详情 html
    def run(self, params):

        act = params['act']
        self.date = getCurrentTime(frm="%Y%m%d")  # 获取日期
        if act == "list":
            self.getList()
            self.parseInfo()
        elif act == "parse":
            self.parseInfo()

    def getList(self):
        """ 获取列表 """
        config = self.url
        # 拼接路径
        path_root = config['path'] + self.date  # 保存路径
        path_list = path_root + "/list"  # 列表路径
        path_info = path_root + "/info"  # 详情路径
        path_json = path_root + "/json"  # json 路径
        path_vid = path_root + "/vid"  # vid 路径
        # 创建目录
        self.makeSuredirs(path_root)
        self.makeSuredirs(path_list)
        self.makeSuredirs(path_info)
        self.makeSuredirs(path_json)
        self.makeSuredirs(path_vid)

        pages = range(1, config['num'] + 1)  # 获取页数

        # 遍历页数,保存到本地
        for idx in pages:
            tmp_path = path_list + "/" + str(idx)  # 以分页页码为文件名
            tmp_url = config['url'].replace("#d#", str(idx))  # 替换页码
            app.logger.info("get list : " + tmp_url)
            if os.path.exists(tmp_path):
                continue

            tmp_content = self.getHttpContent(tmp_url)
            self.saveContent(tmp_path, tmp_content)
            time.sleep(0.3)

        # 遍历 list 目录，解析列表
        for idx in os.listdir(path_list):
            tmp_content = self.getContent(path_list + "/" + str(idx))
            items_data = self.parseList(tmp_content)  # 解析列表
            if not items_data:
                continue

            for item in items_data:
                tmp_json_path = path_json + "/" + item['hash']  # 保存 json 路径
                tmp_info_path = path_info + "/" + item['hash']  # 保存 info 路径
                tmp_vid_path = path_vid + "/" + item['hash']  # 保存 vid 路径
                if not os.path.exists(tmp_json_path):
                    self.saveContent(tmp_json_path, json.dumps(item, ensure_ascii=False))  # 保存 json

                if not os.path.exists(tmp_info_path):
                    tmp_content = self.getHttpContent(item['url'])
                    self.saveContent(tmp_info_path, tmp_content)  # 保存 info

                if not os.path.exists(tmp_vid_path):
                    tmp_content = self.getHttpContent(item['vid_url'])
                    self.saveContent(tmp_vid_path, tmp_content)  # 保存 vid

                time.sleep(0.3)

    def parseList(self, content):
        """ 解析列表 """
        data = []
        config = self.url  # 获取配置
        url_info = urlparse(config['url'])
        url_domain = url_info[0] + "://" + url_info[1]  # 获取域名 http://www.btbtdy.me

        tmp_soup = BeautifulSoup(str(content), "html.parser")  # 解析 html
        tmp_list = tmp_soup.select("div.list_su ul li")  # 获取列表 dom
        for tmp_item in tmp_list:
            tmp_target = tmp_item.select("a.pic_link")  # 获取 a 标签
            tmp_name = tmp_target[0]['title']  # 获取标题
            tmp_href = tmp_target[0]['href']  # 获取链接
            if "http:" not in tmp_href:
                tmp_href = url_domain + tmp_href  # 拼接链接
            tmp_vid_url = tmp_href.replace("btdy/dy", "vidlist/")  # 替换链接
            tmp_data = {
                "name": tmp_name,
                "url": tmp_href,
                "vid_url": tmp_vid_url,
                "hash": hashlib.md5(tmp_href.encode("utf-8")).hexdigest()  # 生成 hash, 用于唯一标识
            }
            data.append(tmp_data)

        return data

    def parseInfo(self):
        """ 解析详情信息 """
        config = self.url
        path_root = config['path'] + self.date
        path_info = path_root + "/info"
        path_json = path_root + "/json"
        path_vid = path_root + "/vid"

        # 遍历 info 目录，解析详情
        for filename in os.listdir(path_info):
            tmp_json_path = path_json + "/" + filename
            tmp_info_path = path_info + "/" + filename
            tmp_vid_path = path_vid + "/" + filename

            tmp_data = json.loads(self.getContent(tmp_json_path))  # 读取 json
            tmp_content = self.getContent(tmp_info_path)  # 读取 info
            tmp_soup = BeautifulSoup(tmp_content, "html.parser")  # 解析 html
            try:
                tmp_pub_date = tmp_soup.select("div.vod div.vod_intro dl dd")[0].getText()  # 获取发布日期
                tmp_desc = tmp_soup.select("div.vod div.vod_intro div.des")[0].getText()  # 获取描述
                tmp_classify = tmp_soup.select("div.vod div.vod_intro dl dd")[2].getText()  # 获取分类
                tmp_actor = tmp_soup.select("div.vod div.vod_intro dl dd")[6].getText()  # 获取演员
                tmp_pic_list = tmp_soup.select("div.vod div.vod_img img")  # 获取图片
                tmp_pics = []  # 图片列表
                for tmp_pic in tmp_pic_list:
                    tmp_pics.append(tmp_pic['src'])

                # 获取下载地址
                tmp_download_content = self.getContent(tmp_vid_path)  # 读取 vid
                tmp_vid_soup = BeautifulSoup(tmp_download_content, "html.parser")
                tmp_download_list = tmp_vid_soup.findAll("a", href=re.compile("magnet:?"))  # 获取磁力链接下载地址
                tmp_magnet_url = ""
                if tmp_download_list:
                    tmp_magnet_url = tmp_download_list[0]['href']  # 获取下载地址

                tmp_data['pub_date'] = tmp_pub_date
                tmp_data['desc'] = tmp_desc
                tmp_data['classify'] = tmp_classify
                tmp_data['actor'] = tmp_actor
                tmp_data['magnet_url'] = tmp_magnet_url
                tmp_data['source'] = self.source
                tmp_data['created_time'] = tmp_data['updated_time'] = getCurrentTime()
                if tmp_pics:
                    tmp_data['cover_pic'] = tmp_pics[0] # 封面图
                    tmp_data['pics'] = json.dumps(tmp_pics) # 图片列表

                tmp_movie_info = Movie.query.filter_by(hash=tmp_data['hash']).first()  # 查询是否存在
                if tmp_movie_info:
                    continue

                tmp_model_movie = Movie(**tmp_data)
                db.session.add(tmp_model_movie)
                db.session.commit()
            except Exception:
                app.logger.exception("parse info failed: %s" % (filename))
                continue
        return True

    def getHttpContent(self, url):
        """ 获取 url 的内容 """
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return None

            return r.content.decode(r.apparent_encoding or 'utf-8', errors='replace')

        except Exception:
            return None

    def saveContent(self, path, content):
        """ 保存内容到文件 """
        if content:
            with open(path, mode="w+", encoding="utf-8") as f:
                if type(content) != str:
                    content = content.decode("utf-8", errors="replace")  # 转换为字符串

                f.write(content)
                f.flush()
                f.close()

    def getContent(self, path):
        """ 读取文件内容 """
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()

        return ''

    def makeSuredirs(self, path):
        """ 创建目录 """
        if not os.path.exists(path):
            os.makedirs(path)
