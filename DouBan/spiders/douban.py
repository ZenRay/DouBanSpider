# -*- coding: utf-8 -*-
import scrapy

import requests
import json
import ssl
import logging
import sys
import re
import redis

from pyquery import PyQuery
from lxml import etree
from urllib import parse
from DouBan.items import CoverImageItem, DoubanDataItem
from DouBan.utils import compress
from DouBan.settings import DEFAULT_REQUEST_HEADERS as HEADERS
from DouBan.settings import DATABASE_CONF

from DouBan.utils.exceptions import ConnectionError

logger = logging.getLogger(__name__)


class DoubanSpider(scrapy.Spider):
    name = 'douban'
    # allowed_domains = ['douban.com', "movie.douban.com/"]
    # start_urls = ['https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%BB%8F%E5%85%B8&sort=recommend&page_limit=20&page_start=0']
    # url = 'http://movie.douban.com/j/search_subjects?type=movie&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start=' + "0"

    tags = list(reversed(["热门", "最新", "经典", "可播放", "豆瓣高分", "冷门佳片", \
            "华语", "欧美", "韩国", "日本", "动作", "喜剧", "爱情", "科幻", "悬疑", \
                "恐怖", "文艺"]))
    page_ends = list(reversed([360, 495, 491, 223, 495, 495, 230, 255, 115, 220, 200, 200, 200, \
                112, 152, 123, 491]))
    _start_url = "http://movie.douban.com/j/search_subjects?type=movie&tag={tag}&sort=recommend&page_limit=20&page_start="

    # connect redis database
    redis_connect = redis.StrictRedis(connection_pool=redis.ConnectionPool(
        **DATABASE_CONF["redis"]))
    # check the connection status
    if not redis_connect.ping():
        raise ConnectionError("Can't connect the redis server. Checkout" + 
                            " network and config parameters.")
    redis_key = DoubanDataItem.__name__

    def start_requests(self):
        for index, tag in enumerate(self.tags):
            # start = 0
            start = 0 #self.page_ends[index]
            tag = parse.quote(tag)
            url = self._start_url.format(tag=tag)
            while start < self.page_ends[index]:
                logger.critical(f"URL: {url+str(start)}")

                yield scrapy.Request(url+str(start), callback=self.item_page)
                # TODO: next page
                start += 1
                

    def parse(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        item = DoubanDataItem()
        item["cover_page"] = response.meta["cover_page"]
        item["url"] = response.url
        item["title"] = response.css('h1 > span::text').extract_first()
        item["release_year"] = response.css('h1 > span::text')[1].re("\d+")[0]
        item["rate"] = response.meta["rate"]
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
            item["play_duration"] = '0'
        elif len(play_duration) == 1:
            item["play_duration"] = play_duration[0]
        else:
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
        # data = {}
        # for name, role in zip(response.css("#celebrities > ul > li > div > span > a::text").extract(), 
        #     response.css("#celebrities > ul > li > div > span::text").extract()):
        #     data[name] = role
        # item["worker_detail"] = json.dumps(data)
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
        
        data = json.loads(response.text)["subjects"]
        item = CoverImageItem()

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
                        "cover_page": page_item["cover"]})

            if not self.redis_connect.sismember(self.redis_key, item["id"]):
                yield scrapy.Request(page_item["url"], callback=self.parse, meta=meta)
            else:
                logger.info(f"{item['id']} Crawled")


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