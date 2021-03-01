# 豆瓣爬虫
解决豆瓣剧集信息抓取，包括豆瓣详情页下的具体的信息以及获取搜索的 JSON 数据。数据存储方面分别存储在了 MySQL 以及 MongoDB 中，前者存储种子信息、详情内容信息，后者存储了大量文档性数据，例如评论信息等

# Requirements

爬取主要依赖于 scrapy，解析搜索部分需要依赖于 JS 中方法调用。整个项目中的依赖包括:

* scrapy >= 2.0.0
* sqlalchemy >= 1.3.16
* pypinyin == 0.37.0
* pymongo
* pymysql
* redis
* requests_html
* execjs

因 JS 的独立运行依赖于 [Node.js](https://nodejs.org/en/download/)，需要安装 `v8.10.0` 版本

# 用例

搜索方式获取数据和详情页内容数据是两种不同的方式，前者是通过 JS 文件进行解码获取数据，后者是直接以种子(即豆瓣影视内容的 ID) 拼接 URL 结合 Scrapy 工作爬取。

## 种子方式请求

种子存储在数据表的 schema 信息如下:

```mysql
CREATE TABLE `series_temp` (
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `title` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视标题',
  `main_tag` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片',
  `crawled` boolean DEFAULT 0 COMMENT '该条目信息是否已经爬取，默认为 0 未爬取，1 为已爬取',
  `priority` boolean DEFAULT 0 COMMENT '该条目信息是否需要优先爬取，默认为 0 不需要优先，1 为优先爬取',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`series_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='外源信息临时存储表';
```

详情页的解析是在 [series.py](./DouBan/DouBan/spiders/series.py) 脚本，需要调用爬取任务时使用 scrapy 启动: `scrapy crawl series`。

## 搜索页面解析

搜索解析是解析影视内容关键字搜索的功能，通过解析关键字搜索的响应结果获取影视内容的 URL。该方式目前是 `utils` 的功能模块，并没有整合到爬虫流程中。此外该模块的调用方式包括给定搜索 URL 或者搜索关键的响应对象：

```python
from urllib import parse
import requests
url = "https://search.douban.com/movie/subject_search?search_text={keyword}&cat=1002"
keyword = "英雄"

from DouBan.utils import search
decrypt = search.Decrypt()

# 方式一: 直接将搜索 URL 作为参数传入
data = decrypt(url.format(keyword=parse.quote(keyword)), method="GET")

# 方式二: 先获取到响应结果，再进行解析
response = requsts.get(url.format(keyword=parse.quote(keyword)))
data = decrypt(response)
```

解析数据的过程中，两者是相同的——都需要通过获取到响应对象进行解析。如果需要其他请求参数，可以使用关键字参数方式调用。