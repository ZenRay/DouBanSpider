# -*- coding: utf-8 -*-
import scrapy

import requests
import requests_html
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
import pymongo
from os import path, remove
from pyquery import PyQuery
from lxml import etree
from urllib import parse
from DouBan.items import (
    CoverImageItem, DouBanDetailItem, ListItem, DouBanAwardItem, DouBanWorkerItem,
    DouBanPeopleItem, DouBanPhotosItem, DouBanEpisodeItem, DouBanCommentsItemM
)
from DouBan.utils import compress
from DouBan.settings import DEFAULT_REQUEST_HEADERS as HEADERS
from DouBan.settings import DATABASE_CONF

from DouBan.utils.exceptions import ConnectionError
from DouBan.utils.pages import *
from DouBan.database.conf import configure

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
        

        # * 需要完成对存储在表中的影视内容进行爬去和解析——用于解析详情内容
        if global_config.getboolean("douban_seed", "check_table"):
            # load 数据管理对象
            from DouBan.database.manager import DataBaseManipulater
            from DouBan.database.manager.datamodel import DouBanSeriesSeed
            manipulater = DataBaseManipulater(echo=False)
            url = "https://movie.douban.com/subject/{seed}/"
            # 从种子数据库中提取未爬取的数据
            with manipulater.get_session() as session:
                # seeds = session.query(DouBanSeriesSeed).filter(DouBanSeriesSeed.crawled == 0).order_by(DouBanSeriesSeed.create_time.desc())
                seed = session.query(DouBanSeriesSeed) \
                    .filter(DouBanSeriesSeed.crawled == 0) \
                    .order_by(DouBanSeriesSeed.create_time.desc())
                
            while seed.count() > 0:
                seed = seed.first()
                yield scrapy.Request(url.format(seed=seed.series_id), \
                    callback=self.detail_page)
                
                # 开发阶段只测试一个源
                if global_config.getboolean("env", "development"):
                    return 
                
                # 请求下一个 seed
                with manipulater.get_session() as session:
                    seed = session.query(DouBanSeriesSeed) \
                            .filter(DouBanSeriesSeed.crawled == 0) \
                            .order_by(DouBanSeriesSeed.create_time.desc()) 

        # * 仅获取到电视剧相关页面的内容保存到数据库以备下一步解析用，不需要进行下一级页面解析
        if global_config.getboolean("douban_seed", "crawl_new"):
            for tag in self.tags:
                start = 0
                while start <= self.end_pages:
                    url = self._start_url.format(tag=tag, page=start * 20)
                    yield scrapy.Request(url, dont_filter=True, \
                        callback=self.list_page, meta={"tag": tag})
                    
                    # 下一页
                    start += 1
                    
                    # 开发阶段只测试一个源
                    if global_config.getboolean("env", "development"):
                        return 
                    

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
        self.logger.info(f"爬取影视条目页面: {response.url}")
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
        if global_config.getboolean("douban_seed", "crawl_img"):
            res = requests.get(item.cover)
            if int(res.status_code) == 200:
                item["cover_content"] = base64.b64encode(res.content)
            else:
                logger.error(f"Request Image content failed:{item.cover}")
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
        
        # 请求获奖详细列表信息
        if response.css("div.mod").re("获奖情况"):
            url = f"https://movie.douban.com/subject/{item['series_id']}/awards/"
            yield scrapy.Request(url, callback=self.parse_awards)

        # 请求演职人员信息
        if response.css("div.celebrities").re("演职员"):
            url = f"https://movie.douban.com/subject/{item['series_id']}/celebrities"
            yield scrapy.Request(url, callback=self.parse_worker)

        # 请求海报和壁纸信息
        url = f"https://movie.douban.com/subject/{item['series_id']}/photos?type="
        types = ["S", "R", "W"]
        
        for type_ in types:
            yield scrapy.Request(url+type_, callback=self.parse_photos, meta={"max_depth":0})

        # 判断页面内容是否有分集(说明是电视剧)
        if response.css("div.article h2 i").re("分集短评"):
            for episode_link in response.css(
                    "div.article > div.episode_list > a::attr(href)"
                ).extract():
                url = f"https://movie.douban.com/{episode_link}"
                yield scrapy.Request(url, callback=self.parse_episode)

        # 评论内容
        url = f"https://movie.douban.com/subject/{item['series_id']}/"
        for query in ["comments?status=P", "comments?status=F", "reviews"]:
            if query.startswith("reviews"):
                yield scrapy.Request(url+query, callback=self.parse_comments)
            else:
                yield scrapy.Request(url+query, callback=self.parse_comments)


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
                # 去重复筛选
                collection = configure.parser.get("mongodb", "person_collection")
                count = self.mongodb_query_count(collection, {"id": worker.id})
                if count == 0:
                    yield scrapy.Request(url.format(id=worker.id), \
                        callback=self.parse_people)
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
        try:
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


            # 判断是否有上传图片，如果有图片那么需要请求图片
            if int(response.css("div#photos > div.hd span > a::text").re("全部(\d+)张")[0]) > 0:
                url = response.url + "photos/"
                yield scrapy.Request(url, callback=self.parse_person_imgs, meta={"data": item})
        except AttributeError as err:
            self.log(f"请求的 URL 错误: {response.url}", level=logging.ERROR)


    def parse_person_imgs(self, response):
        """解析演职人员的图片

        仅保留首页中的图片
        """
        item = response.meta.pop("data")

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
        item["imgs_content"] = contents

        yield item


    def parse_photos(self, response):
        """解析所有相关的图片

        """
        item = DouBanPhotosItem()
        item["sid"] = re.search("subject/(\d{3,})", response.url).group(1)
        type_ = parse.parse_qs(parse.splitquery(response.url)[1])["type"][0]
        
        # 转换图片类型：海报、剧照还是壁纸
        if type_ == "R":
            item["type"] = "海报"
            datum, next_ = Pictures.extract_poster(response)
        elif type_ == "S":
            item["type"] = "剧照"
            datum, next_ = Pictures.extract_wallpaper_and_series_still(response)
        elif type_ == "W":
            item["type"] = "壁纸"
            datum, next_ = Pictures.extract_wallpaper_and_series_still(response)
        
        
        # 遍历获取到数据，转换为 Item
        for data in datum:
            item["pid"] = data.id
            item["url"] = data.url
            item['specification'] = data.specification
            item["content"] = self.request_img_content(data.url)
            item["description"] = data.description

            yield item
        
        # 需要判断是否需要请求下一页，并且请求的深度小于最大深度限制
        if bool(next_) & (response.meta.get("max_depth") < self.config.getint("optional", "crawl_imgs_max_depth")):
            yield scrapy.Request(next_, callback=self.parse_photos, \
                meta={"max_depth": response.meta["max_depth"] + 1})


    def parse_episode(self, response):
        """解析分集信息
        """
        data = Details.extract_episode_info(response)
        item = DouBanEpisodeItem()
        for field in ["sid", "episode", "title", "origin_title", "date", "plot"]:
            item[field] = getattr(data, field)
        
        yield item


    def parse_comments(self, response):
        if "comments" in response.url:
            datum, next_ = Comments.extract_short_comment(response)
        else:
            with requests_html.HTMLSession() as session:
                res = session.get(response.url)
                datum, next_ = Comments.extract_reviews(res, True)
        
        sid = re.search("subject/(\d+)/", response.url).group(1)
        
        for data in datum:
            item = DouBanCommentsItemM(**{field: data._asdict().get(field) if field != "sid" else sid \
                for field in DouBanCommentsItemM.fields})
            # 根据 watched 字段是否为布尔值作为判断是短评论还是影评
            if isinstance(item['watched'], bool):
                item['type'] = "短评论"
                item['content_full'] = None
            else:
                item['type'] = "影评"
                # 获取影评全文
                url = f"https://movie.douban.com/j/review/{item['comment_id']}/full"
                with requests_html.HTMLSession() as session:
                    res = session.get(url)
                    if res.status_code == 200:
                        content = res.json().get('html')
                        item['content_full'] = content
                    else:
                        item['content_full'] = None

            yield item
        
        # 下一页
        if next_:
            yield scrapy.Request(next_, callback=self.parse_comments)



    def request_img_content(self, url):
        """请求图片的内容

        需要根据全局设置判断是否需要获取图片的二进制内容
        """
        result = None
        if self.config.getboolean("optional", "crawl_people_img"):
            res = requests.get(url)
            if int(res.status_code) == 200:
                result = base64.b64encode(res.content)
        
        return result


    def mongodb_query_count(self, table, query:dict):
        """MongoDB 查询满足条件的数量

        查询 MongoDB 数据库中数据是否已经存在，collection 是数据库中的文档名称，query 是
        查询的字典条件, table 对应 mongodb 中的 collection 名称
        """
        # 如果没有链接数据库，那么创建链接
        if not hasattr(self, "database"):
            self.create_mongo_connection()

        collection = self.database[table]
        result = collection.find(query).count()

        return result



    def create_mongo_connection(self):
        """创建 MongoDB 链接
        """
        port = configure.parser.getint("mongodb", "port")
        host = configure.parser.get("mongodb", "host")
        tz_aware = configure.parser.getboolean("mongodb", "tz_aware")
        minPoolSize = configure.parser.getint("mongodb", "minPoolSize")
        database = configure.parser.get("mongodb", "database")
        

        self.mongo_client = pymongo.MongoClient(port=port, host=host, \
            tz_aware=tz_aware, minPoolSize=minPoolSize)
        self.database = self.mongo_client[database]
        