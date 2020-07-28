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
        # TODO: 仅获取到电视剧相关页面的内容保存到数据库以备下一步解析用，不需要进行下一级页面解析
        else:
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


    def parse(self, response):
        pass
