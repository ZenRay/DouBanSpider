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

from os import path, remove
from pyquery import PyQuery
from lxml import etree
from urllib import parse
from DouBan.items import CoverImageItem, DouBanDetailItem
from DouBan.utils import compress
from DouBan.settings import DEFAULT_REQUEST_HEADERS as HEADERS
from DouBan.settings import DATABASE_CONF

from DouBan.utils.exceptions import ConnectionError
from scrapy.exceptions import IgnoreRequest

logger = logging.getLogger(__name__)

# parse the file, so that check whether the addictive file exits
global_config = configparser.ConfigParser()
__filepath = path.join(path.dirname(__file__), "../../scrapy.cfg")

if path.exists(__filepath):
    with open(__filepath, "r") as file:
        global_config.read_file(file)
        movies = None
        # if there is addictive file, get the movies url list
        if global_config.has_option("addictive_movies_file", "path"):
            filename = path.join(path.dirname(__filepath), global_config.get("addictive_movies_file", "path"))
            if path.exists(filename):
                with open(filename, "r") as mfile:
                    movies = [i.strip() for i in mfile.readlines()]

                # if delete file option is True, delete file
                if global_config.getboolean("addictive_movies_file", "delete"):
                    remove(filename)



class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['douban.com', "movie.douban.com/"]

    # TODO: 仅抓取最新的前 10 页电影
    _start_url = "https://movie.douban.com/j/new_search_subjects?sort=R&range=0,10&tags={tag}&start="
    page_ends = [10000]
    tags = ["电影"]
    latest_ends = [10]

    # connect redis database
    redis_connect = redis.StrictRedis(connection_pool=redis.ConnectionPool(
        **DATABASE_CONF["redis"]))
    # check the connection status
    if not redis_connect.ping():
        raise ConnectionError("Can't connect the redis server. Checkout" + 
                            " network and config parameters.")
    redis_key = DouBanDetailItem.__name__

    def start_requests(self):
        # if movies is not None, request the movies url and stop another requests
        if movies:
            for url in movies:
                yield scrapy.Request(url, callback=self.direct_parse_page)
        else:
            for index, tag in enumerate(self.tags):
                # start = 0
                start = 0 #self.page_ends[index]
                tag = parse.quote(tag)
                url = self._start_url.format(tag=tag)
                while start <= self.latest_ends[index]:
                    logger.critical(f"URL: {url+str(start*20)}")
                    yield scrapy.Request(url+str(start * 20), callback=self.item_page)
                    # TODO: next page
                    start += 1
                

    def parse(self, response):
        item = DoubanDataItem()
        item["cover_page"] = response.meta["cover_page"]
        item["url"] = response.url
        # item["title"] = response.css('h1 > span::text').extract_first()
        item["title"] = response.meta["title"]
        item["release_year"] = response.css('h1 > span::text')[1].re("\d+")[0]
        item["rate"] = response.meta["rate"] or None
        item["id"] = response.meta["id"]
        item["rate_collections"] = response.css("div.rating_sum > a.rating_people > span::text").extract_first()
        # parse div#info element that is content
        query = PyQuery(response.text)
        tree = etree.HTML(response.text, etree.HTMLParser())
        content = query("div#info")
        item["director"] = content("span:nth-child(1) > span.attrs > a").text().strip()
        item["screenwriter"] = content("span:nth-child(3)").text().replace(r"编剧:", "").strip()
        item["actors"] = content("span:nth-child(5)").text().replace(r"主演:", "").strip()
        item["category"] = "/".join(response.xpath("//span[@property='v:genre']/text()").extract())
        item["play_location"] = "/".join(response.xpath("//span[@property='v:initialReleaseDate']/text()").re("\((.*)\)"))
        item["play_year"] = "/".join(response.xpath("//span[@property='v:initialReleaseDate']/text()").re("(.*)\("))
        play_duration = response.xpath("//span[@property='v:runtime']/text()").re(".+分钟")
        # parse play_duration time, if None set 0
        if play_duration is None:
            item["play_duration"] = None
        elif len(play_duration) == 1:
            item["play_duration"] = play_duration[0]
        else:
            item["play_duration"] = None
            if not isinstance(play_duration, list):
                logger.warning(f"播放时间解析错误: {play_duration}")

        item["nick_name"] = self.check(tree, "又名")
        item["product_country"] = self.check(tree, "制片国家/地区")
        item["language"]= self.check(tree, "语言")

        # parse imdb URL 
        imdb_item = response.css("div#info > a:last-of-type")
        # imdb_item = tree.cssselect("div#info > span:last-of-type + a:first-of-type")
        if not imdb_item:
            imdb_item = tree.cssselect("div#info > span.pl + a[rel='nofollow']:first-of-type")

        try:
            item["imdb"] = imdb_item[-1].attrib["href"]
        except IndexError:
            item["imdb"] = None
        
        # get abstract introduction
        item["introduction"] = "\n".join(i.strip() for i in response.css("div#link-report > span::text").extract())

        # worker info
        actor_name = response.css("#celebrities > ul > li > div > span > a::text").extract()
        actor_role = response.css("#celebrities > ul > li > div > span::text").extract()
        actor_iamge = response.css("#celebrities > ul > li > a > div.avatar::attr(style)").re(r"url\((.+)\)")
        item["worker_detail"] = compress.compress2json(["name", "role", "img_url"],
                                    [actor_name, actor_role, actor_iamge])

        # award amount
        item["award_amount"] = len(response.css("ul.award"))

        # short comment and vote, comment_author
        comment = []
        for i in response.css("div#hot-comments > div.comment-item"):
            if "data-cid" in i.attrib:
                if len(i.css("p > span")) > 1:
                    comment.append(i.css("p > span.full::text").extract_first())
                else:
                    comment.append(i.css("p > span::text").extract_first())

        vote = response.css("div#hot-comments > div.comment-item > div.comment > h3  span.votes::text").extract()
        comment_author = response.css("div#hot-comments > div.comment-item > div.comment > h3 > span.comment-info > a::text").extract()
        
        # comment rating full score is 50
        comment_rate = []
        for i in response.css("div#hot-comments > div.comment-item > div.comment > h3 > span.comment-info  span.rating"):
            comment_rate.append(float(i.re_first("\d+")))

        # comment time
        comment_time = []
        for i in response.css("div#hot-comments > div.comment-item > div.comment > h3 > span.comment-info  span.comment-time "):
            comment_time.append(i.attrib["title"])
        
        item["short_comment"] = compress.compress2json(
            ["author", "time", "rate", "comment"], 
            [comment_author, comment_time, comment_rate, comment]
        )

        # Long comment, vote and author
        comment_author = response.css("section.reviews div.review-list div.review-item > header.main-hd > a.name::text").extract()
        comment_rate = response.css("section.reviews div.review-list div.review-item > header.main-hd > span::attr(class)").re("\d+")
        comment_time = response.css("section.reviews div.review-list div.review-item > header.main-hd > span:last-of-type::text").extract()
        comment = []
        for element in response.css("section.reviews div.review-list div.review-item > div.main-bd div.short-content"):
            comment.append("".join(i.strip() for i in element.css("::text").extract()))

        comment_url = [f"https://movie.douban.com/j/review/{i}/full" for i in response.css("section.reviews div.review-list div.review-item > div.main-bd > div::attr(data-rid)").extract()]
        item["long_comment"] = compress.compress2json(
            ["author", "time", "rate", "comment", "url"],
            [comment_author, comment_time, comment_rate, comment, comment_url]
        )

        ## types tag
        item["tags"] = response.css("div.tags-body > a::text").extract()

        yield item
    

    def item_page(self, response):
        """Detailed Page"""
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        try:
            data = json.loads(response.text)["subjects"]
        except KeyError as err:
            # category page, the key is data
            data = json.loads(response.text)["data"]

        item = CoverImageItem()

        # if there is not data, return None
        if len(data) == 0:
            tags = ", ".join(parse.parse_qs(response.url)["tags"])
            logger.critical(f"{tags} crawled Done")
             

        for page_item in data:
            item["name"] = page_item["title"]
            item["id"] = page_item["id"]
            item["url"] = page_item["cover"]
            # pass the item to download cover
            # yield item

            # crawl detailed page
            meta = response.meta.copy()
            meta.update({"rate": page_item["rate"], 
                        "id": page_item["id"],
                        "cover_page": page_item["cover"],
                        "title": page_item["title"]})

            if not self.redis_connect.sismember(self.redis_key, item["id"]):
                yield scrapy.Request(page_item["url"], callback=self.parse, meta=meta)
            else:
                logger.info(f"{item['id']} Crawled")


    def direct_parse_page(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        item = DoubanDataItem()
        item["cover_page"] = response.css("div#mainpic  img::attr(src)").get() # response.meta["cover_page"]
        item["url"] = response.url
        # item["title"] = response.css('h1 > span::text').extract_first()
        item["title"] = response.xpath("//span[@property='v:itemreviewed']/text()").extract_first().split()[0] # response.meta["title"]
        item["release_year"] = response.css('h1 > span::text')[1].re("\d+")[0]
        item["rate"] = response.css("div.rating_self > strong::text").extract_first() or None # response.meta["rate"] or None
        item["id"] = [i for i in response.url.split("/") if i][-1] # response.meta["id"]
        item["rate_collections"] = response.css("div.rating_sum > a.rating_people > span::text").extract_first()
        # parse div#info element that is content
        query = PyQuery(response.text)
        tree = etree.HTML(response.text, etree.HTMLParser())
        content = query("div#info")
        item["director"] = content("span:nth-child(1) > span.attrs > a").text().strip()
        item["screenwriter"] = content("span:nth-child(3)").text().replace(r"编剧:", "").strip()
        item["actors"] = content("span:nth-child(5)").text().replace(r"主演:", "").strip()
        item["category"] = "/".join(response.xpath("//span[@property='v:genre']/text()").extract())
        item["play_location"] = "/".join(response.xpath("//span[@property='v:initialReleaseDate']/text()").re("\((.*)\)"))
        item["play_year"] = "/".join(response.xpath("//span[@property='v:initialReleaseDate']/text()").re("(.*)\("))
        play_duration = response.xpath("//span[@property='v:runtime']/text()").re(".+分钟")
        # parse play_duration time, if None set 0
        if play_duration is None:
            item["play_duration"] = None
        elif len(play_duration) == 1:
            item["play_duration"] = play_duration[0]
        else:
            item["play_duration"] = None
            if not isinstance(play_duration, list):
                logger.warning(f"播放时间解析错误: {play_duration}")

        item["nick_name"] = self.check(tree, "又名")
        item["product_country"] = self.check(tree, "制片国家/地区")
        item["language"]= self.check(tree, "语言")

        # parse imdb URL 
        imdb_item = response.css("div#info > a:last-of-type")
        # imdb_item = tree.cssselect("div#info > span:last-of-type + a:first-of-type")
        if not imdb_item:
            imdb_item = tree.cssselect("div#info > span.pl + a[rel='nofollow']:first-of-type")

        try:
            item["imdb"] = imdb_item[-1].attrib["href"]
        except IndexError:
            item["imdb"] = None
        
        # get abstract introduction
        item["introduction"] = "\n".join(i.strip() for i in response.css("div#link-report > span::text").extract())

        # worker info
        actor_name = response.css("#celebrities > ul > li > div > span > a::text").extract()
        actor_role = response.css("#celebrities > ul > li > div > span::text").extract()
        actor_iamge = response.css("#celebrities > ul > li > a > div.avatar::attr(style)").re(r"url\((.+)\)")
        item["worker_detail"] = compress.compress2json(["name", "role", "img_url"],
                                    [actor_name, actor_role, actor_iamge])

        # award amount
        item["award_amount"] = len(response.css("ul.award"))

        # short comment and vote, comment_author
        comment = []
        for i in response.css("div#hot-comments > div.comment-item"):
            if "data-cid" in i.attrib:
                if len(i.css("p > span")) > 1:
                    comment.append(i.css("p > span.full::text").extract_first())
                else:
                    comment.append(i.css("p > span::text").extract_first())

        vote = response.css("div#hot-comments > div.comment-item > div.comment > h3  span.votes::text").extract()
        comment_author = response.css("div#hot-comments > div.comment-item > div.comment > h3 > span.comment-info > a::text").extract()
        
        # comment rating full score is 50
        comment_rate = []
        for i in response.css("div#hot-comments > div.comment-item > div.comment > h3 > span.comment-info  span.rating"):
            comment_rate.append(float(i.re_first("\d+")))

        # comment time
        comment_time = []
        for i in response.css("div#hot-comments > div.comment-item > div.comment > h3 > span.comment-info  span.comment-time "):
            comment_time.append(i.attrib["title"])
        
        item["short_comment"] = compress.compress2json(
            ["author", "time", "rate", "comment"], 
            [comment_author, comment_time, comment_rate, comment]
        )

        # Long comment, vote and author
        comment_author = response.css("section.reviews div.review-list div.review-item > header.main-hd > a.name::text").extract()
        comment_rate = response.css("section.reviews div.review-list div.review-item > header.main-hd > span::attr(class)").re("\d+")
        comment_time = response.css("section.reviews div.review-list div.review-item > header.main-hd > span:last-of-type::text").extract()
        comment = []
        for element in response.css("section.reviews div.review-list div.review-item > div.main-bd div.short-content"):
            comment.append("".join(i.strip() for i in element.css("::text").extract()))

        comment_url = [f"https://movie.douban.com/j/review/{i}/full" for i in response.css("section.reviews div.review-list div.review-item > div.main-bd > div::attr(data-rid)").extract()]
        item["long_comment"] = compress.compress2json(
            ["author", "time", "rate", "comment", "url"],
            [comment_author, comment_time, comment_rate, comment, comment_url]
        )

        ## types tag
        item["tags"] = response.css("div.tags-body > a::text").extract()

        yield item


    def check(self, tree, target:str):
        """Check Information validate
        
        Check whether the target name exits, if it exits, return the value else
        return None.

        Arguments:
            tree: element tree object
            target: string, it's the name that need to be checked 
        
        Results:
            return None, if target doesn't exist, or get the value
        """
        for item in tree.cssselect("div#info > span"):
            if item.text and target in item.text:
                return item.xpath("./following-sibling::text()")[0].strip()
        else:
            return None