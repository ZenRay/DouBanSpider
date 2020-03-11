# -*- coding: utf-8 -*-
import scrapy

import requests
import json
import ssl

import sys

from urllib import parse

from DouBan.settings import DEFAULT_REQUEST_HEADERS as HEADERS

class DoubanSpider(scrapy.Spider):
    name = 'douban'
    # allowed_domains = ['douban.com', "movie.douban.com/"]
    # start_urls = ['https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%BB%8F%E5%85%B8&sort=recommend&page_limit=20&page_start=0']
    # url = 'http://movie.douban.com/j/search_subjects?type=movie&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start=' + "0"

    tags = ["热门", "最新", "经典", "可播放", "豆瓣高分", "冷门佳片", \
            "华语", "欧美", "韩国", "日本", "动作", "喜剧", "爱情", "科幻", "悬疑", \
                "恐怖", "文艺"]
    _start_url = "http://movie.douban.com/j/search_subjects?type=movie&tag={tag}&sort=recommend&page_limit=20&page_start={start}"


    def start_requests(self):
        # TODO: ===== 下面的代码是请求部分代码，暂时进行注释
        for tag in self.tags:
            start = 0
            while True:
                tag = parse.quote(tag)
                start *= 20
                url = self._start_url.format(tag=tag, start=start)
                
                yield scrapy.Request(url, callback=self.item_page)
                break
            break
                # response = requests.get(url, headers=HEADERS)
                
                # next page
                # start += 1


        # yield scrapy.Request(self.url, callback=self.parse)


    def parse(self, response):
        print(response.text)
        # print(json.loads(response.text))
        from scrapy.shell import inspect_response
        inspect_response(response, self)
        pass
    
    def item_page(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)
        
        data = json.loads(response.text)["subject"]
        
        for detail_page in data:
            
        pass