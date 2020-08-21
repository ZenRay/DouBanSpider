#coding:utf8
"""
MySQL 数据表的数据模型:
1. TempItem 是 `series_temp` 表的数据库模型
"""
import sqlalchemy
import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func

# declarative Base
Base = declarative_base()



class DouBanSeriesSeed(Base):
    """外源信息临时表

    外源信息临时表，用于存储需要影视信息种子源。表名是 `series_temp`，schema 信息可以通过
    `douban_series.sql` 文件中确认
    """
    __tablename__ = "series_seed"
    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(length=20, convert_unicode=True), nullable=False, unique=True)
    title = sqlalchemy.Column(sqlalchemy.VARCHAR(150, convert_unicode=True, collation="utf8mb4"), nullable=False)
    main_tag = sqlalchemy.Column(sqlalchemy.VARCHAR(10, convert_unicode=True, collation="utf8mb4"), nullable=True)
    status = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    create_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=func.now())
    update_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


    def __repr__(self):
        format = "<Data Model Object: %s at %s>"
        return format % (self.__class__.__tablename__, hex(id(self)))

    def __str__(self):
        string = f"Item data:\n\t ID: {self.id} Series_ID: {self.series_id}" + \
                f" Title: {self.title} Status: {self.status}"
        return string


class DoubanSeries(Base):
    """影视数据表"""
    __tablename__ = "series_info"

    # id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(20), comment="豆瓣影视 ID", primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.VARCHAR(length=150, convert_unicode=True, collation="utf8mb4"), nullable=False, comment="豆瓣影视名称")
    alias = sqlalchemy.Column(sqlalchemy.VARCHAR(length=150, convert_unicode=True, collation="utf8mb4"), comment="豆瓣影视别名")
    rate = sqlalchemy.Column(sqlalchemy.DECIMAL(2, 1), comment='豆瓣影视评分')
    rate_collection = sqlalchemy.Column(sqlalchemy.Integer(unsigned=True), default=0, comment='豆瓣影视评论人数')
    main_tag = sqlalchemy.Column(sqlalchemy.VARCHAR(10, convert_unicode=True), comment='豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片')
    genres = sqlalchemy.Column(sqlalchemy.VARCHAR(200, convert_unicode=True), comment='豆瓣影视类型，例如 恐怖、动作等')
    product_country = sqlalchemy.Column(sqlalchemy.VARCHAR(100, convert_unicode=True), comment='豆瓣影视制片国家')
    language = sqlalchemy.Column(sqlalchemy.VARCHAR(100, convert_unicode=True), comment='豆瓣影视语言')
    release_year = sqlalchemy.Column(sqlalchemy.YEAR(display_width=4), comment='豆瓣影视成片年份')
    release_date = sqlalchemy.Column(sqlalchemy.VARCHAR(100), comment='豆瓣影视上映日期，不同的国家可能日期不同')
    play_duration = sqlalchemy.Column(sqlalchemy.VARCHAR(100), comment='豆瓣影视播放时长，可能不同回家版本存在不同时长')
    imdb_id = sqlalchemy.Column(sqlalchemy.VARCHAR(20), comment='IMDB 数据中的 ID')
    tags = sqlalchemy.Column(sqlalchemy.VARCHAR(100), comment='豆瓣影视中豆瓣成员常用标签 实际可能为豆瓣处理得到的结果')
    directors = sqlalchemy.Column(sqlalchemy.VARCHAR(100, convert_unicode=True, collation="utf8mb4"), comment='豆瓣影视条目中导演，使用 / 分隔')
    screenwriter = sqlalchemy.Column(sqlalchemy.VARCHAR(100, collation="utf8mb4", convert_unicode=True), comment='豆瓣影视条目中编剧，使用 / 分隔')
    actors = sqlalchemy.Column(sqlalchemy.VARCHAR(150, collation="utf8mb4", convert_unicode=True), comment='豆瓣影视条目中演员，使用 / 分隔')
    plot = sqlalchemy.Column(sqlalchemy.VARCHAR(300, collation="utf8mb4", convert_unicode=True), comment='豆瓣影视条目剧情简介')
    cover = sqlalchemy.Column(sqlalchemy.VARCHAR(150, collation="utf8mb4", convert_unicode=True), comemnt='豆瓣影视条目中封面海报链接')
    official_site = sqlalchemy.Column(sqlalchemy.VARCHAR(200, collation="utf8mb4", convert_unicode=True), comemnt='影视条目上的官方网站')
    recommendation_type = sqlalchemy.Column(sqlalchemy.VARCHAR(20), comment=' 提取豆瓣推荐的类型，解析的内容页面上提供的"好于"类型的信息')
    recommendation_item = sqlalchemy.Column(sqlalchemy.VARCHAR(300), comment="提取豆瓣对当前内容推荐对相似条目")
    episode_info = sqlalchemy.Column(sqlalchemy.VARCHAR(300, convert_unicode=True), comment="提取电视剧的各集剧情信息")
    create_time = sqlalchemy.Column(sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据')
    update_time = sqlalchemy.Column(sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), comment='更新爬取时间，没有更新的情况和首次爬取时间一致')
    


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{name}(id='{id}', series_id='{series_id}', title=" + \
            "'{title}', cover='{cover}', create_time='{create_time}')>"
        items = {key: self.__getattribute__(key) for key in self.__dir__() \
            if not key.startswith("_")}

        return format_.format(name=self.__tablename__, **items)

    
    def __eq__(self, other):
        """比较两个对象是不是相等
        """
        return self.series_id == other.series_id