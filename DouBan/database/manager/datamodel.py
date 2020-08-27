#coding:utf8
"""
MySQL 数据表的数据模型:
1. TempItem 是 `series_temp` 表的数据库模型
"""
import sqlalchemy
import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from sqlalchemy.dialects.mysql import INTEGER, YEAR, TINYINT
from sqlalchemy.orm import relationship, backref

# declarative Base
Base = declarative_base()


__all__ = ["Base", "DouBanSeriesSeed", "DouBanSeriesList", "DouBanSeriesInfo", \
    "DouBanEpisodeInfo", "DouBanSeriesWorker", "DouBanSeriesPic", "DouBanSeriesPerson", \
    "DouBanSeriesAwards"]
class DouBanSeriesSeed(Base):
    """外源信息临时表

    外源信息临时表，用于存储需要影视信息种子源。表名是 `series_temp`，schema 信息可以通过
    `douban_series.sql` 文件中确认
    """
    __tablename__ = "series_temp"
    __table_args__ = {'mysql_engine': 'InnoDB'}
    
    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(20), primary_key=True, comment="豆瓣影视 ID")
    title = sqlalchemy.Column(
        sqlalchemy.VARCHAR(150, convert_unicode=True, collation="utf8mb4_general_ci"), 
        nullable=False, comment="豆瓣影视标题"
    )
    tag = sqlalchemy.Column(
        sqlalchemy.VARCHAR(10, convert_unicode=True, collation="utf8mb4_general_ci"), 
        nullable=True, comment="豆瓣电视剧页面中的 tag，包括 热门,美剧,英剧,韩剧,日剧,国产剧,港剧,日本动画,综艺,纪录片"
    )
    crawled = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    create_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, \
        server_default=func.now())
    update_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, \
        server_default=func.now(), onupdate=func.now())


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    def __str__(self):
        string = f"Item data:\n\t Series_ID: {self.series_id} Title: {self.title}" + \
                f" Status: {self.crawled} Updated: {self.update_time}"
        return string



class DouBanSeriesList(Base):
    """影视在各分类页下列表

    存储的信息为 `list_series` 是用于解决
    1. 存储各分类页下的各 item 的基本信息，例如所有分类下
    https://movie.douban.com/tag/#/ 中请求的内容实际是接口链接，得到的数据是基本的信息:
    https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start=0
    2. 用于判断相关内容是否爬取
    详细 Schema 参考 `douban_series.sql` 文件中的内容。
    """
    __tablename__ = "list_series"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(20), primary_key=True, comment="豆瓣影视 ID")
    tag = sqlalchemy.Column(sqlalchemy.VARCHAR(10, convert_unicode=True), comment='豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片')
    name = sqlalchemy.Column(sqlalchemy.VARCHAR(length=150, convert_unicode=True, collation="utf8mb4_general_ci"), nullable=False, comment="豆瓣影视名称")
    rate = sqlalchemy.Column(sqlalchemy.DECIMAL(2, 1), comment='豆瓣影视评分')
    cover = sqlalchemy.Column(sqlalchemy.VARCHAR(150, convert_unicode=True), comment='豆瓣影视条目中封面海报链接')
    crawled = sqlalchemy.Column(sqlalchemy.BOOLEAN(create_constraint=True), default=False, nullable=False, comment="是否已经爬取")
    create_time = sqlalchemy.Column(sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据')
    update_time = sqlalchemy.Column(sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), comment='更新爬取时间，没有更新的情况和首次爬取时间一致')


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))


    def __str__(self):
        format_ = "<{tbname}(id='{id}', name='{name}', rate='{rate}'" + \
            " crawled='{crawled}', create_time='{create_time}')>"
        items = {
            "id": self.series_id,
            "name": self.name,
            "crawled": self.crawled,
            "rate": self.rate,
            "create_time": self.create_time
        }

        return format_.format(tbname=self.__tablename__, **items)  


class DouBanSeriesInfo(Base):
    """影视数据表
    
    关于豆瓣影视的列表信息
    """
    __tablename__ = "series_info"
    __table_args__ = {'mysql_engine': 'InnoDB'}
    
    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(20), comment="豆瓣影视 ID", primary_key=True)
    name = sqlalchemy.Column(
        sqlalchemy.VARCHAR(length=150, convert_unicode=True, \
            collation="utf8mb4_general_ci"), nullable=False, comment="豆瓣影视名称"
    )
    alias = sqlalchemy.Column(
        sqlalchemy.VARCHAR(length=150, convert_unicode=True, \
            collation="utf8mb4_general_ci"), comment="豆瓣影视别名"
    )
    rate = sqlalchemy.Column(sqlalchemy.DECIMAL(2, 1), comment='豆瓣影视评分')
    rate_collection = sqlalchemy.Column(
        INTEGER(unsigned=True), default=0, comment='豆瓣影视评论人数'
    )
    main_tag = sqlalchemy.Column(
        sqlalchemy.VARCHAR(10, convert_unicode=True), \
            comment='豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片'
    )
    genres = sqlalchemy.Column(
        sqlalchemy.VARCHAR(200, convert_unicode=True), comment='豆瓣影视类型，例如 恐怖、动作等'
    )
    product_country = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100, convert_unicode=True), comment='豆瓣影视制片国家'
    )
    language = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100, convert_unicode=True), comment='豆瓣影视语言'
    )
    release_year = sqlalchemy.Column(YEAR(display_width=4), comment='豆瓣影视成片年份')
    release_date = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100), comment='豆瓣影视上映日期，不同的国家可能日期不同'
    )
    play_duration = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100), comment='豆瓣影视播放时长，可能不同回家版本存在不同时长'
    )
    imdb_id = sqlalchemy.Column(sqlalchemy.VARCHAR(20), comment='IMDB 数据中的 ID')
    tags = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100), comment='豆瓣影视中豆瓣成员常用标签 实际可能为豆瓣处理得到的结果'
    )
    directors = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100, convert_unicode=True, collation="utf8mb4_general_ci"), \
            comment='豆瓣影视条目中导演，使用 / 分隔'
    )
    screenwriters = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100, collation="utf8mb4_general_ci", convert_unicode=True), 
        comment='豆瓣影视条目中编剧，使用 / 分隔'
    )
    actors = sqlalchemy.Column(
        sqlalchemy.VARCHAR(400, collation="utf8mb4_general_ci", convert_unicode=True), 
        comment='豆瓣影视条目中演员，使用 / 分隔'
    )
    plot = sqlalchemy.Column(
        sqlalchemy.VARCHAR(3000, collation="utf8mb4_general_ci", convert_unicode=True), 
        comment='豆瓣影视条目剧情简介'
    )
    cover = sqlalchemy.Column(
        sqlalchemy.VARCHAR(150), comment='豆瓣影视条目中封面海报链接'
    )
    cover_content = sqlalchemy.Column(
        sqlalchemy.BLOB, nullable=True, comment="豆瓣影视海报链接请求后的 content，避免后续无法请求的情况" 
    )
    official_site = sqlalchemy.Column(
        sqlalchemy.VARCHAR(200, convert_unicode=True), \
            comment='影视条目上的官方网站'
    )
    recommendation_type = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), comment='提取豆瓣推荐的类型，解析的内容页面上提供的"好于"类型的信息'
    )
    recommendation_item = sqlalchemy.Column(
        sqlalchemy.VARCHAR(300, collation="utf8mb4_general_ci", convert_unicode=True), \
            comment="提取豆瓣对当前内容推荐对相似条目"
    )

    create_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据'
    )
    update_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), \
            comment='更新爬取时间，没有更新的情况和首次爬取时间一致'
    )
    

    episodes = relationship("DouBanEpisodeInfo", backref="episode_info", lazy="joined")
    workers = relationship("DouBanSeriesWorker", backref="worker", lazy="joined")
    picutres = relationship("DouBanSeriesPic", backref="picture", lazy="joined")
    awards = relationship("DouBanSeriesAwards", backref="award", lazy="joined")

    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{tbname} (%s)>".format(tbname=self.__tablename__)

        items = ", ".join(f"{key}='{self.__getattribute__(key)}'" \
            for key in self.__dir__() if not key.startswith("_"))
        return format_ % items

    
    def __eq__(self, other):
        """比较两个对象是不是相等
        """
        return self.series_id == other.series_id


class DouBanEpisodeInfo(Base):
    """豆瓣电视剧剧集信息

    电视剧集在每一集存在不同的信息，因为单独存放在 `episode_info` 中
    """
    __tablename__ = "episode_info"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True,autoincrement=True)
    sid = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), \
        sqlalchemy.ForeignKey("series_info.series_id", onupdate="CASCADE", ondelete="RESTRICT"), \
        nullable=False, comment='豆瓣影视剧条目 ID'
    )
    episode = sqlalchemy.Column(TINYINT(3, unsigned=True), nullable=False, comment='多季剧集集数')
    title = sqlalchemy.Column(
        sqlalchemy.VARCHAR(150, collation="utf8mb4_general_ci", convert_unicode=True), 
        comment='影视剧集标题', default=None
    )
    origin_title = sqlalchemy.Column(
        sqlalchemy.VARCHAR(150, collation="utf8mb4_general_ci", convert_unicode=True), 
        comment='影视剧集原始标题，主要是一类国外剧集的标题', default=None
    )
    date = sqlalchemy.Column(
        sqlalchemy.VARCHAR(200, convert_unicode=True, collation="utf8mb4_general_ci"), 
        default=None, comment="剧集上映日期"
    )

    plot = sqlalchemy.Column(
        sqlalchemy.VARCHAR(3000, collation='utf8mb4_general_ci', convert_unicode=True), 
        default=None, comment='豆瓣影视条目多季剧集剧情简介'
    )
    create_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据'
    )
    update_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), \
            comment='更新爬取时间，没有更新的情况和首次爬取时间一致'
    )
    
    # episode_redirect = relationship("DoubanSeriesInfo", back_populates="series_id", \
    #     passive_deletes=True)


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{tbname} (%s)>".format(tbname=self.__tablename__)

        items = ", ".join(f"{key}='{self.__getattribute__(key)}" \
            for key in self.__dir__() if not key.startswith("_"))
        return format_ % items



class DouBanSeriesWorker(Base):
    """豆瓣影视演职人员信息"""
    __tablename__ = "worker"
    __table_args__ = {"mysql_engine": "InnoDB"}

    wid = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), nullable=False, comment='豆瓣影视演职人员 ID',
        primary_key=True
    )

    sid = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), \
        sqlalchemy.ForeignKey("series_info.series_id", onupdate="CASCADE", ondelete="RESTRICT"), \
        nullable=False, comment='豆瓣影视剧条目 ID'
    )
    
    name = sqlalchemy.Column(
        sqlalchemy.VARCHAR(25, convert_unicode=True, collation="utf8mb4_general_ci"),
        nullable=False, comment='豆瓣影视演职人员姓名'
    )
    
    alias = sqlalchemy.Column(
        sqlalchemy.VARCHAR(40, convert_unicode=True, collation="utf8mb4_general_ci"),
        default=None, comment='豆瓣影视演职人员姓名(非中文)'
    )

    duty = sqlalchemy.Column(sqlalchemy.VARCHAR(100), comment='演职人员岗位')

    action = sqlalchemy.Column(
        sqlalchemy.VARCHAR(5), default=None, comment='演员或其他配音演员，参与到影片中到方式'
    )

    role = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100), default=None, comment='演员或其他配音演员，在影片中的角色'
    )

    create_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据'
    )
    update_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), \
            comment='更新爬取时间，没有更新的情况和首次爬取时间一致'
    )
    
    # work_redirect = relationship("DoubanSeriesInfo", back_populates="series_id", \
    #     passive_deletes=True)


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{tbname} (%s)>".format(tbname=self.__tablename__)

        items = ", ".join(f"{key}='{self.__getattribute__(key)}" \
            for key in self.__dir__() if not key.startswith("_"))
        return format_ % items 


class DouBanSeriesPic(Base):
    """影视内容的图片信息"""
    __tablename__ = "picture"
    __table_args__ = {"mysql_engine": "InnoDB"}

    pid = sqlalchemy.Column(
        sqlalchemy.VARCHAR(30), nullable=False, primary_key=True, \
        comment="影视海报和壁纸 ID"
    )

    sid = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), \
        sqlalchemy.ForeignKey("series_info.series_id", onupdate="CASCADE", ondelete="RESTRICT"), \
        nullable=False, comment='豆瓣影视剧条目 ID'
    )

    url = sqlalchemy.Column(
        sqlalchemy.VARCHAR(150), nullable=False, comment='海报和壁纸的链接'
    )

    content = sqlalchemy.Column(
        sqlalchemy.BLOB, nullable=True, comment="豆瓣影视海报和壁纸的链接请求后的 content，避免后续无法请求的情况"
    )

    description = sqlalchemy.Column(
        sqlalchemy.VARCHAR(40, convert_unicode=True, collation="utf8mb4_general_ci"), \
            default=None, comment='豆瓣影视海报和壁纸的描述信息'
    )

    specification = sqlalchemy.Column(
        sqlalchemy.VARCHAR(30), default=None, comment="影视海报和壁纸原始规格描述"
    )

    type = sqlalchemy.Column(
        sqlalchemy.VARCHAR(10), default=None, comment="影视图片类型：海报、壁纸或者剧照"
    )
    create_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据'
    )
    update_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), \
            comment='更新爬取时间，没有更新的情况和首次爬取时间一致'
    )

    # pic_redirect = relationship("DoubanSeriesInfo", back_populates="series_id", \
    #     passive_deletes=True)

    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{tbname} (%s)>".format(tbname=self.__tablename__)

        items = ", ".join(f"{key}='{self.__getattribute__(key)}" \
            for key in self.__dir__() if not key.startswith("_"))
        return format_ % items 



class DouBanSeriesPerson(Base):
    """影视演职人员 Profile 信息"""
    __tablename__ = "person"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), primary_key=True, comment='豆瓣影视演职人员的 ID'
    )

    name = sqlalchemy.Column(
        sqlalchemy.VARCHAR(25, convert_unicode=True, collation="utf8mb4_general_ci"),
        nullable=False, comment= '豆瓣影视演职人员姓名'
    )

    gender = sqlalchemy.Column(
        TINYINT(1, unsigned=True), nullable=False, default=2, 
        comment='演职人员性别, 1 为男性，0 为女性, 2 为未标注，默认为 2'
    )

    constellation = sqlalchemy.Column(
        sqlalchemy.VARCHAR(5, convert_unicode=True), default=None, \
            comment='影视演职人员的星座'
    )
    
    birthdate = sqlalchemy.Column(
        sqlalchemy.DATE, default=None, comment='影视演职人员出生日期'
    )

    birthplace = sqlalchemy.Column(
        sqlalchemy.VARCHAR(30), default=None, comment='影视演职人员出生地'
    )

    profession = sqlalchemy.Column(
        sqlalchemy.VARCHAR(40), default=None, comment='演职人员的职业名称，可能使用 / 分隔'
    )
    
    alias = sqlalchemy.Column(
        sqlalchemy.VARCHAR(160, convert_unicode=True, collation="utf8mb4_general_ci"),
        default=None, comment='豆瓣影视演职人员姓名(非中文)'
    )

    alias_cn = sqlalchemy.Column(
        sqlalchemy.VARCHAR(240, convert_unicode=True, collation="utf8mb4_general_ci"),
        default=None, comment='豆瓣影视演职人员姓名(中文)'
    )

    family = sqlalchemy.Column(
        sqlalchemy.VARCHAR(100, convert_unicode=True, collation="utf8mb4_general_ci"),
        default=None, comment="豆瓣影视演职人员家庭成员"
    )

    imdb_link = sqlalchemy.Column(
        sqlalchemy.VARCHAR(30), default=None, comment='IMDB 数据中 ID'
    )

    official_web = sqlalchemy.Column(
        sqlalchemy.VARCHAR(150), default=None, comment='影视推广的官方网站'
    )

    introduction = sqlalchemy.Column(
        sqlalchemy.VARCHAR(3000, collation="utf8mb4_general_ci", convert_unicode=True),
        default=None, comment="人物信息简介"
    )

    create_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据'
    )
    update_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), \
            comment='更新爬取时间，没有更新的情况和首次爬取时间一致'
    ) 


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{tbname} (%s)>".format(tbname=self.__tablename__)

        items = ", ".join(f"{key}='{self.__getattribute__(key)}" \
            for key in self.__dir__() if not key.startswith("_"))
        return format_ % items 


class DouBanSeriesAwards(Base):
    """影视获奖列表信息"""
    __tablename__ = "award"
    __table_args__ = {"mysql_engine": "InnoDB"} 

    id = sqlalchemy.Column(
        sqlalchemy.BIGINT, primary_key=True, comment='豆瓣影视演职人员的 ID',
        autoincrement=True
    )


    sid = sqlalchemy.Column(
        sqlalchemy.VARCHAR(20), \
        sqlalchemy.ForeignKey("series_info.series_id", onupdate="CASCADE", ondelete="RESTRICT"), \
        nullable=False, comment='豆瓣影视剧条目 ID'
    )

    host = sqlalchemy.Column(
        sqlalchemy.VARCHAR(40, collation="utf8mb4_general_ci", convert_unicode=True),
        nullable=False, comment='颁奖主办方'
    )

    year = sqlalchemy.Column(
        YEAR(display_width=4), default=None, comment='获奖年份'
    )

    name = sqlalchemy.Column(
        sqlalchemy.VARCHAR(30, collation="utf8mb4_general_ci", convert_unicode=True),
        nullable=False, comment='获奖类型名称'
    )

    person = sqlalchemy.Column(
        sqlalchemy.VARCHAR(60, collation="utf8mb4_general_ci", convert_unicode=True),
        default=None, comment='获奖人姓名'
    )

    status = sqlalchemy.Column(
        TINYINT(1), nullable=False, default=1, comment='最终获奖状态, 1 为获奖，0 表示只有提名'
    )

    create_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), comment='首次爬取数据'
    )
    update_time = sqlalchemy.Column(
        sqlalchemy.DATETIME, server_default=func.now(), onupdate=func.now(), \
            comment='更新爬取时间，没有更新的情况和首次爬取时间一致'
    ) 


    def __repr__(self):
        format = "<%s data model object at %s>"
        return format % (self.__class__.__name__, hex(id(self)))

    
    def __str__(self):
        format_ = "<{tbname} (%s)>".format(tbname=self.__tablename__)

        items = ", ".join(f"{key}='{self.__getattribute__(key)}" \
            for key in self.__dir__() if not key.startswith("_"))
        return format_ % items