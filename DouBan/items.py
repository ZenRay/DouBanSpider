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
    series_id = scrapy.Field() # 豆瓣影视 ID
    name = scrapy.Field()
    alias = scrapy.Field()
    rate = scrapy.Field()
    rate_collection = scrapy.Field()
    main_tag = scrapy.Field() # 豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片
    genres = scrapy.Field() # 豆瓣影视类型，例如 恐怖、动作等
    product_country = scrapy.Field()
    language = scrapy.Field()
    release_year = scrapy.Field()
    release_date = scrapy.Field()   # 豆瓣影视上映日期，不同的国家可能日期不同
    play_duration = scrapy.Field()  # 豆瓣影视播放时长，可能不同回家版本存在不同时长
    imdb_id = scrapy.Field()    # IMDB 数据中的 ID
    tags = scrapy.Field()   # 豆瓣影视中豆瓣成员常用标签 实际可能为豆瓣处理得到的结果
    directors = scrapy.Field()  # 豆瓣影视条目中导演，使用 / 分隔
    screenwriters = scrapy.Field() # 豆瓣影视条目中编剧，使用 / 分隔
    actors = scrapy.Field() # 豆瓣影视条目中演员，使用 / 分隔
    plot = scrapy.Field()   # 豆瓣影视条目剧情简介
    cover = scrapy.Field()  # 豆瓣影视条目中封面海报链接
    cover_content = scrapy.Field()  # 豆瓣影视海报链接请求后的 content，避免后续无法请求的情况
    official_site = scrapy.Field()  # 影视条目上的官方网站
    recommendation_type = scrapy.Field()
    recommendation_item = scrapy.Field()



class CoverImageItem(scrapy.Item):
    id = scrapy.Field(serializer=str)
    name = scrapy.Field(serializer=str)
    url = scrapy.Field(serializer=str)
