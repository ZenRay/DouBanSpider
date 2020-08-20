# -*- coding: utf-8 -*-
import scrapy

import requests
import json
import ssl
import logging
import sys
import re
import redis
import configparser

import numbers
from os import path, remove
from pyquery import PyQuery
from lxml import etree
from urllib import parse
from DouBan.items import CoverImageItem, DoubanDataItem, ListItem
from DouBan.utils import compress
from DouBan.settings import DEFAULT_REQUEST_HEADERS as HEADERS
from DouBan.settings import DATABASE_CONF

from DouBan.utils.exceptions import ConnectionError
from scrapy.exceptions import IgnoreRequest

logger = logging.getLogger("Douban " + __name__)

# parse the file, so that check whether the addictive file exits
global_config = configparser.ConfigParser()
__filepath = path.join(path.dirname(__file__), "../../scrapy.cfg")

if path.exists(__filepath):
    with open(__filepath, "r") as file:
        global_config.read_file(file)
        series = None
        # if there is addictive file, get the movies url list
        if global_config.has_option("addictive_series_file", "path"):
            filename = path.join(path.dirname(__filepath), global_config.get("addictive_series_file", "path"))
            if path.exists(filename):
                with open(filename, "r") as mfile:
                    series = [i.strip() for i in mfile.readlines()]

                # if delete file option is True, delete file
                if global_config.getboolean("addictive_series_file", "delete"):
                    remove(filename)


class SeriesSpider(scrapy.Spider):
    """
    豆瓣电视剧部分
    """
    name = 'series'
    allowed_domains = ['movie.douban.com', "douban.com"]

    tags = ["热门","美剧","英剧","韩剧","日剧","国产剧","港剧","日本动画","综艺","纪录片"]
    end_pages = 500
    _start_url = "https://movie.douban.com/j/search_subjects?type=tv&tag={tag}&sort=time&page_limit=20&page_start={page}"
    

    def start_requests(self):
        """
        如果存在待处理的 sereis 信息，优先处理
        """
        if series:
            for url in series:
                yield scrapy.Request(url, callback=self.direct_parse_page)
        
        # TODO: 需要完成对存储在表中的电视剧内容进行爬去和解析——用于解析详情内容
        if global_config.getboolean("addictive_series_file", "check_table"):
            pass

        # * 仅获取到电视剧相关页面的内容保存到数据库以备下一步解析用，不需要进行下一级页面解析
        if global_config.getboolean("addictive_series_file", "crawl_new"):
            for tag in self.tags:
                start = 0
                while start <= self.end_pages:
                    url = self._start_url.format(tag=tag, page=start * 20)
                    yield scrapy.Request(url, dont_filter=True, \
                        callback=self.list_page, meta={"tag": tag})
                    
                    # 下一页
                    start += 1
                    

    def list_page(self, response):
        """
        用于解析详情页内容，不解析具体的详情内容
        """

        # 解析列表页中的 list
        data = json.loads(response.body_as_unicode()).get("subjects", [])
        item = ListItem()
        
        for element in data:
            # 更新item 数据
            item["tag"] = response.meta["tag"]
            item["title"] = element["title"]
            item["url"] = element["url"]
            item["list_id"] = element["id"]
            item["cover_url"] = element["cover"]
            item["rate"] = float(element["rate"]) if len(element["rate"])>0 else None
            
            yield item


    def detail_page(self, response):
        """
        处理详情页面的内容
        """


    def parse(self, response):
        pass





#* 需要再次请求的信息
# ! 剧评(长评论)的页面 URL: https://movie.douban.com/subject/{影视 ID}/reviews
    # 需要注意长评论的 headers 需要重新调整
    """
    headers = {
        "Host": "movie.douban.com",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://movie.douban.com/subject/4739952/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    """
    # ! 长评论接口，需要用 div[@data-cid] 的值去拼接: https://movie.douban.com/j/review/{data-cid}/full 
    # id: 影视 ID

# ! 电视剧各集详情，在详情页通过 id 和集数值拼接：https://movie.douban.com/subject/{影视 ID}/episode/{集数值}/
    # id: 影视 ID
        # episode: 集数
        # title_cn: 当前集的中文标题
        # title_origin: 当前集的原始标题，主要指原始语言标题
        # play_date: 播放日期
        # introduction: 内容简介
# ! 海报，通过详情页的 id 拼接，此外页面上有显性的下一页: 
# !   https://movie.douban.com/subject/{影视 id}/photos?type=R  以及 https://movie.douban.com/subject/{影视 id}/photos?type=W
    # id: 影视 ID
        # url: 图片链接，需要在页面内搜索 li[@data-id]拼接 https://img1.doubanio.com/view/photo/l/public/p{data-id}.webp
        # type: 图片来源，海报或者壁纸
# ! 演职人员信息，通过详情页的 id 拼接，相关角色通过页面解析: https://movie.douban.com/subject/{影视 ID}/celebrities
    # id: 影视 ID
        # name: 姓名
        # celebrity_id: 姓名对应的 ID，需要从链接中解析仅保存其中的 ID
        # duty: 职能，例如: 导演、演员、配音 等
        # role: 角色，某些职能不参与影视内角色，可以是空
# ! 提名以及获奖信息，通过详情页的 id 拼接，: https://movie.douban.com/subject/{影视 ID}/awards/
    # id: 影视 ID
        # time: 获奖或提名时间
        # host: 主办方以及时期，eg: 第65届黄金时段艾美奖
        # name: 获奖获提名信息
        # receiver: 获奖人姓名以及 id(仅存储 celebrity 之后的 id), 以 dict 存储{'name':<name>, 'id':<id>}
