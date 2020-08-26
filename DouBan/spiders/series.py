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
import base64
import string
import numpy as np

import numbers
from os import path, remove
from pyquery import PyQuery
from lxml import etree
from urllib import parse
from DouBan.items import (
    CoverImageItem, DouBanDetailItem, ListItem, DouBanAwardItem, DouBanWorkerItem,
    DouBanPeopleItem
)
from DouBan.utils import compress
from DouBan.settings import DEFAULT_REQUEST_HEADERS as HEADERS
from DouBan.settings import DATABASE_CONF

from DouBan.utils.exceptions import ConnectionError
from DouBan.utils.pages import *

from scrapy.exceptions import IgnoreRequest



logger = logging.getLogger("Douban " + __name__)

# parse the file, so that check whether the addictive file exits
global_config = configparser.ConfigParser()
__filepath = path.join(path.dirname(__file__), "../../scrapy.cfg")

if path.exists(__filepath):
    global_config.read(__filepath)
    series = None
    # if there is addictive file, get the movies url list
    if global_config.has_option("addictive_series", "path"):
        filename = path.join(path.dirname(__filepath), global_config.get("addictive_series", "path"))
        if path.exists(filename):
            with open(filename, "r") as mfile:
                series = [i.strip() for i in mfile.readlines()]

            # if delete file option is True, delete file
            if global_config.getboolean("addictive_series", "delete"):
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
    
    # 配置文件传输，设置为属性方式传递
    config = global_config
    def start_requests(self):
        """
        如果存在待处理的 series 信息，优先处理
        """
        if series:
            for url in series:
                yield scrapy.Request(url, callback=self.direct_parse_page)
        

        # TODO: 需要完成对存储在表中的电视剧内容进行爬去和解析——用于解析详情内容
        if global_config.getboolean("addictive_series", "check_table"):
            # 数据管理对象
            from DouBan.database.manager import DataBaseManipulater
            from DouBan.database.manager.datamodel import DouBanSeriesSeed
            manipulater = DataBaseManipulater(echo=True)
            url = "https://movie.douban.com/subject/{seed}/"
            # 从种子数据库中提取未爬取的数据
            with manipulater.get_session() as session:
                seeds = session.query(DouBanSeriesSeed).filter(DouBanSeriesSeed.crawled == 0)
                # ! debugger
                # import numpy as np
                for seed in seeds.all():
                    yield scrapy.Request(url.format(seed=seed.series_id), \
                        callback=self.detail_page, meta={"session": session})
                    
                    # ! Debugger
                    break


        # * 仅获取到电视剧相关页面的内容保存到数据库以备下一步解析用，不需要进行下一级页面解析
        if global_config.getboolean("addictive_series", "crawl_new"):
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
            item["rate"] = float(element["rate"]) if len(element["rate"]) > 0 else None
            
            yield item


    def detail_page(self, response):
        """
        处理详情页面的内容
        """
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        item = DouBanDetailItem()
        item["series_id"] = re.search("subject/(\d{3,})", response.url).group(1)
        item["name"] = Details.extract_title(response).name
        item["alias"] = Details.extract_nick_name(response)
        item["rate"] = Details.extract_rate(response)
        item["rate_collection"] = Details.extract_rate_collections(response)
        # 需要在后续根据分类页面的内容重新调整，目前暂时只提取电视剧和电影的分类
        item["main_tag"] = Details.extract_main_tag(response)
        item["genres"] = Details.extract_genres(response)
        item["product_country"] = Details.extract_product_country(response)
        item["language"] = Details.extract_language(response)
        item["release_year"] = Details.extract_release_year(response)

        # 如果能提取到日期数据，转换为 JSON 数据
        item["release_date"] = json.dumps(Details.extract_release_date(response), \
            ensure_ascii=False)

        item["play_duration"] = Details.extract_play_duration(response)
        item["imdb_id"] = Details.extract_imdb_id(response)
        item["tags"] = Details.extract_tags(response) 

        directors = Details.extract_directors(response)
        if directors:
            item["directors"] = "/".join(i.name for i in directors)
        else:
            item["directors"] = None

        screenwriters = Details.extract_screenwriter(response)
        if screenwriters:
            item["screenwriters"] = "/".join(i.name for i in screenwriters)
        else:
            item["screenwriters"] = None
        
        actors = Details.extract_actors(response)
        if actors:
            item["actors"] = "/".join(i.name for i in actors)
        else:
            item["actors"] = None

        item["plot"] = Details.extract_plot(response)
        item["cover"] = Details.extract_cover_url(response)
        
        # * 根据 crawl_img 选项判断是否需要将图片链接转换为实际请求的内容
        if global_config.getboolean("addictive_series", "crawl_img"):
            res = requests.get(item.cover)
            if int(res.status_code) == 200:
                item["cover_content"] = base64.b64encode(res.content)
            else:
                logger.debug(f"Request Image content failed:{item.cover}")
                item["cover_content"] = None

        item["official_site"] = Details.extract_official_web(response)

        item["recommendation_type"] = Details.extract_recommendation_type(response)
        recommendation_items = Details.extract_recommendation_item(response) 

        if recommendation_items:
            item["recommendation_item"] = json.dumps(
                {i.id:i.name for i in recommendation_items}, ensure_ascii=False
            )
        else:
            item["recommendation_item"] = None
        yield item
        # import ipdb; ipdb.set_trace()
        # 请求获奖详细列表信息
        if response.css("div.mod").re("获奖情况"):
            url = f"https://movie.douban.com/subject/{item['series_id']}/awards/"
            yield scrapy.Request(url, callback=self.parse_awards)

        # 请求演职人员信息
        if response.css("div.celebrities").re("演职员"):
            url = f"https://movie.douban.com/subject/{item['series_id']}/celebrities"
            yield scrapy.Request(url, callback=self.parse_worker)


    def parse_awards(self, response):
        """解析获奖信息
        """
        item = DouBanAwardItem()
        for award in Awards.extract_awards(response):
            item["sid"] = re.search("subject/(\d+)", response.url).group(1)
            item["host"] = award.host
            item["year"] = award.year
            item["name"] = award.name
            item["person"] = award.person
            item["status"] = award.status

            yield item


    def parse_worker(self, response):
        """解析演职人员信息

        解析演职人员基本信息之前，需要将各个演职人员的 profile 信息写入 people 表中，因此设计
        爬取流程上需要在生成 item 数据之前完成爬取
        """
        item = DouBanWorkerItem()
        # 对演员的角色进行调整，使用 mapping 加快搜索
        duties = {duty.id:duty for duty in Workers.extract_duties(response)}
        # profile 页面链接
        url = "https://movie.douban.com/celebrity/{id}/"

        for worker in Workers.extract_basic(response):
            if worker.id is None:
                logger.debug(f"{worker.name} 没有ID信息，随机生成一个 15 位 ID")
                id = "".join(np.random.choice(list(string.ascii_letters), 15))
            else:
                id = worker.id

            item["wid"] = id
            item["name"] = worker.name
            item["alias"] = worker.alias
            item["sid"] = re.search("subject/(\d{3,})", response.url).group(1)
            item["duty"] = duties[worker.id].duty if duties.get(worker.id) else None
            item["action"] = duties[worker.id].action if duties.get(worker.id) else None
            item["role"] = duties[worker.id].role if duties.get(worker.id) else None

            # 请求 profile 页面信息
            if worker.id is not None:
                yield scrapy.Request(url.format(id=worker.id), callback=self.parse_people)
            else:
                people = DouBanPeopleItem({
                    "id":id, "name": worker.name, "gender": 2
                })
                yield people
            
            # 传递获取到的 item 数据
            yield item


    def parse_people(self, response):
        """解析演职人员 Profile 页面

        """
        item = DouBanPeopleItem()
        data = People.extract_bio_informaton(response)

        item["id"] = data.id
        item["name"] = data.name
        # 调整性别值为整型数据
        if data.gender is None:
            gender = 2
        elif "男" in data.gender:
            gender = 1
        else:
            gender = 0

        item["gender"] = gender
        item["constellation"] = data.constellation
        item["birthdate"] = data.birthdate
        item["birthplace"] = data.birthplace
        item["profession"] = data.profession
        item["alias"] = data.alias
        item["alias_cn"] = data.alias_cn
        item["family"] = data.family
        item["imdb_link"] = data.imdb_link
        item["official_web"] = data.official_web
        item["introduction"] = data.introduction

        yield item

        # 判断是否有上传图片，如果有图片那么需要请求图盘
        if int(response.css("div#photos > div.hd span > a::text").re("全部(\d+)张")[0]) > 0:
            yield scrapy.Request(url, callback=self.parse_person_imgs)


    def parse_person_imgs(self, response):
        """解析演职人员的图片

        仅保留首页中的图片
        """
        item = DouBanPeopleItem()
        id = re.search("/celebrity/(\d+)/", response.url).group(1)
        imgs = response.css(
            "div.article > ul.clearfix > li > div.cover img::attr(src)"
        ).extract()

        if self.config.getboolean("optional", "crawl_people_img"):
            contents = []
            for link in imgs:
                res = requests.get(link)
                if int(res.status_code) == 200:
                    contents.append(base64.b64encode(res.content))
                else:
                    contents.append(None)
        else:
            contents = None

        item["imgs"] = imgs
        item["id"] = id
        item["imgs_content"] = contents

        yield item




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
