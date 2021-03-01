# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import json



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


class DouBanDetailItem(scrapy.Item):
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
    set_number = scrapy.Field() # 豆瓣影视剧集总集数
    cover = scrapy.Field()  # 豆瓣影视条目中封面海报链接
    cover_content = scrapy.Field()  # 豆瓣影视海报链接请求后的 content，避免后续无法请求的情况
    official_site = scrapy.Field()  # 影视条目上的官方网站
    recommendation_type = scrapy.Field()
    recommendation_item = scrapy.Field()


class DouBanAwardItem(scrapy.Item):
    """获奖信息 Item"""
    sid = scrapy.Field() # 豆瓣影视剧 ID
    host = scrapy.Field()   # 颁奖主办方
    year = scrapy.Field()   # 获奖年份
    name = scrapy.Field()   # 获奖类型名称
    person = scrapy.Field() # 获奖人姓名
    status = scrapy.Field() # 最终获奖状态, 1 为获奖，0 表示只有提名
    

class DouBanWorkerItem(scrapy.Item):
    """演职人员简介信息 Item
    
    是属于简介信息，并不是详细的 profile 信息
    """
    wid = scrapy.Field()    # 豆瓣影视演职人员 ID
    name = scrapy.Field()    # 豆瓣影视演职人员姓名
    alias = scrapy.Field()  # 豆瓣影视演职人员姓名(非中文)
    sid = scrapy.Field()    # 豆瓣影视剧条目 ID
    duty = scrapy.Field()   # 演职人员岗位
    action = scrapy.Field() # 演员或其他配音演员，参与到影片中到方式
    role = scrapy.Field()   # 演员或其他配音演员，在影片中的角色


class DouBanPeopleItem(scrapy.Item):
    """演职人员 profile 的 Item
    """
    id = scrapy.Field() # 豆瓣影视演职人员 ID
    name = scrapy.Field()   # 豆瓣影视演职人员姓名
    gender = scrapy.Field() # 豆瓣演职人员性别  
    constellation = scrapy.Field()  # 星座
    birthdate = scrapy.Field()  # 出生日期
    birthplace = scrapy.Field() # 出生地
    profession = scrapy.Field() # 职业
    alias = scrapy.Field()  # 别名
    alias_cn = scrapy.Field()   # 中文别名
    family = scrapy.Field() # 家庭成员
    imdb_link = scrapy.Field()  # IMDB 数据中 ID
    official_web = scrapy.Field()   # 官方网站
    introduction = scrapy.Field()   # 简介
    imgs = scrapy.Field() # 演职人员图片链接
    imgs_content = scrapy.Field() # 链接转换为已经请求的内容


class DouBanPhotosItem(scrapy.Item):
    """豆瓣影视图片
    
    """
    pid = scrapy.Field()    # 图片链接，保存的数据形式为 array
    sid = scrapy.Field()    # 影视 ID
    url = scrapy.Field()    # 原始图片链接
    content = scrapy.Field()    # 图片的请求到的二进制内容
    description = scrapy.Field() # 图片描述性信息
    specification = scrapy.Field()  # 图片规格
    type = scrapy.Field()   # 当前页面爬取的类型，包括了剧照、海报和壁纸


    
class DouBanEpisodeItem(scrapy.Item):
    """豆瓣电视剧分集信息
    """
    sid = scrapy.Field()    # 影视 ID
    episode = scrapy.Field()    # 剧集集数
    title = scrapy.Field()  # 剧集标题
    origin_title = scrapy.Field()   # 原始标题，可能是非中文标题
    date = scrapy.Field()   # 播放日期
    plot = scrapy.Field()   # 剧情简介



class DouBanCommentsItemM(scrapy.Item):
    """豆瓣用户影视评论内容

    包括短评论：想看和已看的短评论内容
    影评：对影视内容的长评论
    综合短评论和影评的字段信息如下:
        * sid 影视 ID
        * uname 用户名
        * uid 用户链接
        * upic 用户头像
        * date 用户评论日期
        * comment_id 用户评论内容的 ID
        * title 影评的标题，短评是没有标题的
        * content 用户评论的内容
        * content_url 影评的 URL，可以获取影评全文
        * content_full 影评全文
        * rate 评分
        * thumb 赞同评论的用户数量
        * down 不赞同该评论的数量
        * reply 回复该评论的数量
        * watched 短评用户是否已经观看过影视内容，False 表示想看，True 表示看过
        * type 评论的类型，包括了两个方面，短评论和影评
    """
    sid = scrapy.Field()    
    uname = scrapy.Field() 
    uid = scrapy.Field() 
    upic = scrapy.Field()   
    date = scrapy.Field()   
    comment_id = scrapy.Field() 
    title = scrapy.Field()  
    content = scrapy.Field()    
    content_url = scrapy.Field()
    content_full = scrapy.Field()
    rate = scrapy.Field()   
    thumb = scrapy.Field()  
    down = scrapy.Field()   
    reply = scrapy.Field()   
    watched = scrapy.Field()
    type = scrapy.Field() 




class CoverImageItem(scrapy.Item):
    id = scrapy.Field(serializer=str)
    name = scrapy.Field(serializer=str)
    url = scrapy.Field(serializer=str)
