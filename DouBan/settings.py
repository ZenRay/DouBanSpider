# -*- coding: utf-8 -*-

# Scrapy settings for DouBan project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'DouBan'

SPIDER_MODULES = ['DouBan.spiders']
NEWSPIDER_MODULE = 'DouBan.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'DouBan (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 16
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36",
    "Accept": "*/*",
    'Cache-Control': "no-cache",
    "Host": "movie.douban.com",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'DouBan.middlewares.DoubanSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'DouBan.middlewares.UserAgentDownloaderMiddleware': 2,
    # 'DouBan.middlewares.ProxyDownloaderMiddleware': 555,
    # 'DouBan.middlewares.DoubanDownloaderMiddleware': 543,
   
}
# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "DouBan.pipelines.DoubanStoragePipeline": 251,
#    'DouBan.pipelines.DoubanPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Log config
from os import path
# LOG_ENABLED = True
# LOG_ENCODING = "utf8"
# LOG_LEVEL = "INFO"
# LOG_FILE = path.join(path.dirname(__file__), "log/douban.log")


# DataBase configuration
DATABASE_CONF = {
  # basic mysql configuration
  "mysql": {
    "host": "192.168.1.31",
    "port": 3306,
    "user": "root",
    "password": "rpInT6msZU",
    "charset": "utf8mb4",
    "use_unicode": True,
    "database": "hzjy_test"
  },
  "redis": {
      "host": "192.168.1.31",
      "port": 6379,
      "password": None,
      "max_connections": None, # use to initial connection pool
  }
}

TABLE_FIELDS = {
    # 影视基本信息: Done
    "video": {
        "name": "title",
        "name_jane": "name_jane",
        "score": "rate",
        "content_abstract": "introduction",
        "alias_name":  "nick_name",
        "image_path": "cover_page",
        "language": "language"
    },
    # 地区扩展信息字段: Done
    "video_extension_region": {
        "video_id": "video_id",
        "region": "region",     # 需要通过 play_location 拆分以及 play_year 中是否也有 - 判断 
        "year": "release_year",
        "release_time": "release_time", # 需要对 play_year 中是否有 - 判断是否需要删除
        "running_time": "play_duration", 
        "coming_soon": "coming_soon", # 暂时没有爬取该数据，统一为 0
    },
    # 影视演员字段: Done
    "video_actor":{
        "video_id": "video_id",
        "name": "name", # 需要拆分 actors 中的演员信息
        "name_jane": "name_jane", # 需要对 演员信息进行解析
    },
    # 影视导演字段: Done
    "video_director": {
        "video_id": "video_id", # video 表解析
        "name": "name", # 需要通过 director 解析是否为多个导演，目前得到的结果是一个字符串
        "name_jane": "name_jane" # 需要对该字段进行解析 首字母
    },
    # 类型信息字段: Done
    "video_type": {
        "video_id": "video_id", # video 表解析
        "name": "name", # 需要对类型 category 拆分，分隔符为 /
    },
    # 影视短评字段: Done
    "video_review": {
        "video_id": "video_id", # 需要 video 表解析
        "sorting": "sorting", # 直接使用 enumerate 获取评论的索引
        "review_time": "review_time", # short_comment 中解析 time 数据
        "score": "score", # short_comment 中解析 rate 数据
        "content": "content", # short_comment 中解析 comment 数据
    },
    # 影视主要演职员信息字段: Done
    "video_character": {
        "video_id": "video_id", # 需要 video 表解析
        "sorting": "sorting", # 需要对 worker_detail 解析，通过 enumerate 获取索引
        "name": "name", # 需要对 worker_detail 解析，获取到人员姓名信息
        "role": "role", # 需要对 worker_detail 解析，获取到人员角色信息
        "image_path": "image_path", # 保存在不同的源目录下，例如豆瓣的信息， 在 douban 的 characters 目录下，格式是 actor 表中 ID <actor_id>.jpg。目前暂存 URL
    }
}
