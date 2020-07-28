# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy



class ListItem(scrapy.Item):
    """
    豆瓣影视内容列表数据
    """
    tag=scrapy.Field(serializer=str) # 豆瓣页面的 tag
    title=scrapy.Field(serializer=str) # 影视内容标题
    list_id=scrapy.Field(serializer=str) # 影视内容中 ID，由豆瓣提供
    rate=scrapy.Field(serializer=str) # 影视内容评分
    url=scrapy.Field(serializer=str) # 影视列表中各条目的 URL
    cover_url = scrapy.Field(serializer=str) # 影视列表中各条目的海报 URL


class DoubanDataItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()
    id = scrapy.Field() # 源数据的 ID
    title = scrapy.Field() # 名称
    release_year = scrapy.Field() # 标题中上映年份
    rate = scrapy.Field() # 评分
    director = scrapy.Field() # 导演
    screenwriter = scrapy.Field() # 编剧
    actors = scrapy.Field() # 演员
    play_location = scrapy.Field() # 上映日期中的国家
    category = scrapy.Field()   # 类型
    play_year = scrapy.Field()  # 上映日期中国的时间
    play_duration = scrapy.Field()  # 播放时间
    nick_name = scrapy.Field()  # 别名
    product_country = scrapy.Field()    # 制片地区
    language = scrapy.Field()       # 语言
    imdb = scrapy.Field()       # IMDB 链接
    introduction = scrapy.Field()   # 简介
    worker_detail = scrapy.Field()  # 主要演职人员信息， JSON 数据
    award_amount = scrapy.Field()   # 获奖数量
    short_comment = scrapy.Field()  # 短评信息，JSON 数据
    long_comment = scrapy.Field()   # 长评论信息，JSON 数据
    tags = scrapy.Field()           # 标签
    rate_collections = scrapy.Field()   # 评论人员数量

    # 辅助字段信息
    actors_id = scrapy.Field()  # 需要提取演员的 ID
    director_id = scrapy.Field()    # 需要提取导演的 ID
    video_id = scrapy.Field()       # 需要提取 video 的 ID
    cover_page = scrapy.Field()     # 影视海报



class CoverImageItem(scrapy.Item):
    id = scrapy.Field(serializer=str)
    name = scrapy.Field(serializer=str)
    url = scrapy.Field(serializer=str)
