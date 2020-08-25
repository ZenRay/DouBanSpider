#coding:utf8
from __future__ import absolute_import
import re
import json
import datetime

from collections import namedtuple
from DouBan.utils.exceptions import LostArgument, ValueConsistenceError

__all__ = ["Details", "Workers", "Pictures", "Comments", "People", "Awards"]
class Details:
    """
    豆瓣影视内容详情页解析，主要功能是解决 Scrapy 得到 response 之后进行页面解析，得到相应的结果:
    * extract_title, 提取影视标题
    * extract_rate, 提取影视评分
    * extract_rate_collections, 提取影视评分人数
    * extract_cover_url, 提取影视详情页的海报链接
    * extract_genres, 提取类型信息
    * extract_product_country, 提取制片国家信息
    * extract_language, 提取语言信息
    * extract_release_year, 提取成片年份
    * extract_release_date, 提取影片播放日期，存在不同地区播放日期差异
    * extract_play_duration, 提取影片播放时长，存在不同地区不同差异
    * extract_nick_name, 影视标题别名
    * extract_imdb_id, 提取 IMDB 的 ID
    * extract_plot, 提取影视剧情简介
    * extract_tags, 提取豆瓣成员标签
    * extract_recommendation_type, 提取豆瓣推荐的类型，解析的内容页面上提供的"好于"类型的信息
    * extract_recommendation_item, 提取豆瓣对当前内容推荐对相似条目
    * extract_episode_info, 提取电视剧的各集剧情信息
    * extract_main_tag, 提取影视属于哪些主标签，例如: 电影、电视剧、综艺、动漫、纪录片以及短片，
        因为种子内容难以解析到具体到数据，直接简要的分类为 电视剧和电影两种类型
    ------如果页面没有演职人员链接时，需要从主页提取相关信息----------
    * extract_directors, 提取导演信息
    * extract_screenwriter, 提取编剧信息
    * extract_actors, 提取演员信息

    Properties:
    --------------
    __recommendation_item: 当前内容推荐的其他相关内容，包括豆瓣 ID 和内容标题名称
    __content_name: 当前内容的名称，name 为页面中条目标题名称，alias 为根据可选名称得到了
            别名
    __people: 演职人员信息，id 演职人员 ID，name 演职人员姓名
    __episode: 剧集简介信息，id 剧集 ID，episode 当前集数，title 当前剧集标题，origin 当
        前剧集原始标题，date 当前剧集播放日期，plot 当前剧集剧情简介
    """
    __recommendation_item = namedtuple("recommendation_item", \
        ["id", "name"])

    __content_name = namedtuple("item_name", ["name", "alias"])
    __people = namedtuple("worker", ["id", "name"])
    __episode = namedtuple("episode", ["id", "episode", "title", "origin", \
        "date", "plot"])

    def __init__(self):
        pass


    @classmethod
    def extract_title(cls, response, origin_title=None):
        """解析响应页面的 title

        Args:
        ---------
        response 响应页面信息
        origin_title 是列表页中的标题名称，作用是提取到别名

        Results:
        ---------
        result: dict，返回标题名称和别名，title、alias

        """
        if response is None:
            raise LostArgument(f"response is missing")

        title = response.css('h1 > span::text').extract_first()

        # * 如果 origin_title 不是缺失的情况下，提取出别名，否则直接返回
        if origin_title is None:
            name = response.css("head > title::text") \
                    .extract_first() \
                    .replace("(豆瓣)", "") \
                    .strip()
            
            alias = title.replace(name, "").strip()
            
            result = cls.__content_name(name=name, alias=alias if alias else None)
        else:
            # 需要确认 origin_title 是否在提取到的标题中，如果不存在则发生值不一致异常
            if origin_title not in title:
                raise ValueConsistenceError(
                f"`title` isn't consistent with `origin_title`. Response URL: {response.url}"
                )
            result = cls.__content_name(name=origin_title, \
                alias=title.replace(origin_title, "").strip())
        return result


    @classmethod
    def extract_rate(cls, response, digit=1):
        """解析响应页面 rate

        解析评分信息，默认保留 1 为小数位，可以通过 digit 申明保留位数

        """
        text = response.css("div.rating_wrap strong::text").extract_first()
        if text is None:
            return None
        
        # 使用正则表达式确保结果是浮点数
        matchobj = re.search("\d+\.\d+", text)
        if matchobj:
            return round(float(matchobj.group()) * 10 ** digit, digit) / (10 ** digit)
        else:
            return None
            
    
    @classmethod
    def extract_rate_collections(cls, response):
        """参与评分的人数
        """
        collections = response.css(
                "div.rating_sum > a.rating_people span::text"
            ).extract_first()

        # 如果有数据值调整为整型数据值
        if collections:
            collections = int(float(collections))

        return collections


    @classmethod
    def extract_genres(cls, response):
        """提取类型信息
        
        如果存在多个类型，使用 slash 分隔
        """
        if not response.css("div#info > span.pl").re("类型"):
            return None
        
        return "/".join(response.css("span[property='v:genre']::text").extract())


    @classmethod
    def extract_product_country(cls, response):
        """提取制片国家信息

        如果存在多个国家，使用 slash 分隔
        """
        result = response.xpath(
            "//div[@id='info']//span[text()='制片国家/地区:']/following-sibling::text()"
        ).extract_first().strip()
        
        return  result.replace(" / ", "/")


    @classmethod
    def extract_language(cls, response):
        """提取语言信息

        存在多个语言时，使用 slash 分隔
        """
        result = response.xpath(
            "//div[@id='info']//span[text()='语言:']/following-sibling::text()"
        ).extract_first()
        
        if result:
            result = result.strip().replace(" / ", "/")
        
        return result


    @classmethod
    def extract_release_year(cls, response):
        """提取年份信息

        保留成片年份信息为整型数据
        """
        text = response.css(
                "div#content > h1 >span.year::text"
            ).extract_first()

        return int(float(re.sub("\(|\)", "", text)))


    @classmethod
    def extract_release_date(csl, response):
        """提取播放日期

        提取具体的播放日期信息，信息可能分为不同国家地区或者版本信息，而存在差异。如果内容在一
        个国家有多个播放信息，在国家名称中添加一个 `_{number}`。

        Results:
        ---------
        result: dict, 以国家名称为 key，上映日期为 value
        """
        elements = response.css("span[property='v:initialReleaseDate']::text").extract()
        result = {}
        for index, element in enumerate(elements):
            country = re.search("\((.*)\)", element)
            date = re.search("([\d\-]+)", element)

            if not country and not date:
                continue
            
            value = date.group().strip()
            # 如果没有对应的国家，直接使用 index 来替代
            if country is None:
                result[index] = value
            elif country.group() in result:
                key = f"{country.group(1).strip()}_{index}"
                result[key] = value
            else:
                key = country.group(1).strip()
                result[key] = value

        return result


    @classmethod
    def extract_play_duration(cls, response):
        """提取影片播放时长信息
        
        可能不同时间、国家地区以及版本差异有不同时间长度，使用 slash 分隔。如果是处理电视剧的
        信息，那么提取的方式是筛选出"单集片长:" 的兄弟元素信息，否则就是可以直接提取到 "片
        长:" 元素的兄弟元素 
        """
        result = None
        if response.css("div#info > span").re("单集片长:"):
            result = response.xpath(
                "//div[@id='info']//span[text()='单集片长:']/following-sibling::text()"
            ).extract_first()

        if response.css("div#info > span").re("(?<!单集)片长:"):
            result = response.css(
                    "div#info > span[property='v:runtime']::text"
                ).extract_first()

            additional = response.xpath(
                    "//span[@property='v:runtime']/following-sibling::text()"
                ).extract_first()
            
            # 拼接数据值以及删除多余的空格
            if additional:
                result += additional.replace(" / ", "/")

        if result:
            result = result.strip()
        return result


    @classmethod
    def extract_nick_name(cls, response, optional_name=None):
        """提取别名信息
        
        可能有多个别名，使用 slash 分隔。如果有其他提取到的别名信息直接添加到别名中
        """
        result = response.xpath(
                "//div[@id='info']//span[text()='又名:']/following-sibling::text()"
            ).extract_first()

        if not result and optional_name is None:
            return None
        elif result:
            result = result.strip()
            if optional_name is not None:
                return result.replace(" / ", "/") + f"/{optional_name}"
            else:
                return result.replace(" / ", "/")
        

    @classmethod
    def extract_imdb_id(cls, response):
        """提取 IMDB 的 ID
        """
        result = response.xpath(
                "//div[@id='info']/span[text()='IMDb链接:']/following::a/text()"
            ).extract_first() 
        
        return result


    @classmethod
    def extract_plot(cls, response):
        """提取剧情信息
        """
        # 如果没有相关信息，直接退出
        if not response.css("div.related-info").re("剧情简介"):
            return

        # 如果有隐藏信息返回所有信息，否则即直接提取
        result = response.css(
                "div.related-info > div.indent > span.all::text"
            ).extract()
        # ! 清除掉空格信息，字符长度必须大于 1 而非 0
        result = "\n".join(i.strip() for i in result if len(i.strip()) > 1)

        if result:
            return result
        # 不存在长剧情时，获取未隐藏的剧情
        result = response.css(
                "div.related-info > div.indent > span[property='v:summary']::text"
            ).extract()
        
        # ! 清除掉空格信息，字符长度必须大于 1 而非 0
        result = "\n".join(i.strip() for i in result if len(i.strip()) > 1)
        if result:
            return result
            
        
    @classmethod
    def extract_tags(cls, response):
        """提取豆瓣成员常用标签
        """
        if not response.css("div.tags > h2").re("豆瓣成员常用的标签"):
            return 

        return "/".join(i.strip() for i in \
            response.css("div.tags > div.tags-body > a::text").extract())


    @classmethod
    def extract_directors(cls, response):
        """提取导演信息

        提取导演以及豆瓣的 ID 信息——以导演名称和 ID 构成的 key-value，结果保存为 json 处
        理后的字符串
        """
        # 如果类型是导演存在，再查询到导演信息
        # if Details.check_attribute(response, name="导演", \
        #     query="div#info > span:nth-of-type(1) > span::text"):
        if response.xpath(
                "//div[@id='info']/span/span[contains(text(),'导演')]/text()"
            ).extract_first():
            result = []

            # 遍历导演以及豆瓣导演 ID
            names = response.css(
                    "div#info > span:nth-of-type(1) > span.attrs > a::text"
                ).extract()
            ids_  = response.css(
                    "div#info > span:nth-of-type(1) > span.attrs > a::attr(href)"
                ).extract()
            for name, id_ in zip(names, ids_):
                id_ = None if "search_text" in id_ else re.search(r"\d+", id_).group().strip()
                result.append(cls.__people(id=id_, name=name.strip()))

            return result


    @classmethod
    def extract_screenwriter(cls, response):
        """提取页面的编剧信息
        """
        # 如果类型是编剧存在，再查询编剧信息
        # if Details.check_attribute(response, name="编剧", \
        #     query="div#info > span:nth-of-type(2) > span::text"):
        #     result = []
        if response.xpath(
                "//div[@id='info']/span/span[contains(text(),'编剧')]/text()"
            ).extract_first():

            names = response.xpath(
                    "//div[@id='info']//span[contains(text(),'编剧')]/parent::span/span[@class='attrs']/a/text()"
                ).extract()

            ids_ = response.xpath(
                "//div[@id='info']//span[contains(text(),'编剧')]/parent::span/span[@class='attrs']/a/attribute::href"
            ).extract()

            result = []
            for name, id_ in zip(names, ids_):
                id_ = None if "search_text" in id_ else re.search(r"\d+", id_).group().strip()
                result.append(cls.__people(name=name.strip(), id=id_))

            return result


    @classmethod
    def extract_actors(cls, response):
        """提取演员信息
        """
        # 如果类型是演员存在，再查询演员信息
        # if Details.check_attribute(response, name="主演", \
        #     query="div#info > span:nth-of-type(3) > span::text"):
        if response.xpath(
                "//div[@id='info']/span[@class='actor']/span[contains(text(),'主演')]/text()"
            ).extract_first():
            result = []

            names = response.xpath(
                    "//div[@id='info']/span[@class='actor']/span[@class='attrs']/a/text()"
                ).extract()

            ids = response.xpath(
                "//div[@id='info']/span[@class='actor']/span[@class='attrs']/a/attribute::href"
            ).extract()

            for name, id_ in zip(names, ids):
                id_ = None if "search_text" in id_ else re.search(r"\/(\d{2,})\/", id_).group(1).strip()
                result.append(cls.__people(name=name.strip(), id=id_))

            return result

    @classmethod
    def extract_recommendation_type(cls, response):
        """提取豆瓣推荐类型信息
        """
        result = "/".join(i.strip() for i in response.css(
                "div#interest_sectl > div.rating_betterthan > a::attr(href)"
            ).re("[\u2E80-\uFAFF]+"))
        
        if result:
            return result


    @classmethod
    def extract_recommendation_item(cls, response):
        """提取根据当前内容推荐的相关内容
        """
        elements = response.css(
                "div.article > div#recommendations > div.recommendations-bd > dl"
            )

        if elements:
            result = []
            ids = [element.css("dd>a:nth-of-type(1)::attr(href)") \
                .re("subject\/(\d{2,})\/")[0].strip() for element in elements]
            names = [element.css("dd>a:nth-of-type(1)::text") \
                .extract_first().strip() for element in elements]
            
            for name, id in zip(names, ids):
                result.append(cls.__recommendation_item(name=name, id=id))
            return result

    @classmethod
    def extract_cover_url(cls, response):
        """提取详情页海报链接
        """
        link = response.xpath(
            "//div[@id='mainpic']/a/img[contains(attribute::title, '点击看更多海报')]" + 
            "/attribute::src | //div[@id='mainpic']/a/img[contains(attribute::title," +
            " '点击看大图')]/attribute::src"
        ).extract_first()
        
        if link:
            link = link.strip()
        return link


    @staticmethod
    def check_attribute(response, query, name):
        """检查 css 得到的文本值

        确认从 response 的 css 中查询得到的字符串是否为查询到的 name，如果是则返回 True，
        否则返回 False

        Args:
        ---------
        response: URL 响应的页面
        query: str, css 查询语句
        name: str, 查询的目标名称
        """
        text = response.css(query).extract_first()
        
        if name in text:
            return True
        else:
            return False


    @classmethod
    def extract_episode_info(cls, response):
        """提取电视剧剧集信息

        需要请求的链接: https://movie.douban.com/subject/{影视 ID}/episode/{episode}/
        提取剧集各集的介绍，包括影视的 ID，影视集数，影视当前集数标题，当前影视原始标题以及播
        放日期、剧情简介
        """
        id = re.search("subject\/(\d{2,})\/episode", response.url).group(1)
        episode = re.search("episode\/(\d{1,3})", response.url).group(1)
        # 判断是否有中文名
        if cls.check_attribute(response, name="本集中文名:", query= \
            "div.article > ul.ep-info > li:nth-of-type(1) > span:nth-of-type(1)::text"):
            title = response.css(
                    "div.article > ul.ep-info > li:nth-of-type(1) > span.all::text"
                ).extract_first()
            if title:
                title = title.strip()
        else:
            title = None
        
        # 判断是否有原始名称 
        origin = response.css(
                    "div.article > ul.ep-info > li:nth-of-type(2) > span.all::text"
                ).extract_first()
        if origin:
            origin = origin.strip()
        
        # 播放时间
        element = response.xpath(
            "//div[@class='article']/ul[@class='ep-info']/li[position()=3]/span[@class='all']"
        )
        if element:
            date = element.xpath("./text()").extract_first().strip() + " " + \
                element.xpath("./following-sibling::text()").extract_first().strip()
            # 如果有确认播放时间区域，需要添加上相关信息
            local = response.css(
                    "div.article > ul.ep-info > li:nth-of-type(3) > span.note::text"
                ).extract_first()
            if local:
                date += " " + local.strip()
        else:
            date = None
        

        # 剧情信息
        plot = response.css("div.article > ul.ep-info p#link-report") \
                        .css("span.all::text").extract_first()

        if plot:
            plot = plot.strip()
            # 如果有隐藏信息需要添加上
            more = "\n".join(i.strip() for i in \
                element.css("span.hide::text").extract())
            if more:
                plot += more.strip()
        

        result = cls.__episode(id=id, episode=episode, title=title, \
            origin=origin, date=date, plot=plot)

        return result


    @classmethod
    def extract_main_tag(cls, response):
        """提取主要类型

        只需要保留为电视剧和电影两个主要即可
        """
        return  response.xpath(
            "//a[contains(text(), '分享到')]/attribute::data-type"
        ).extract_first()


    @classmethod
    def extract_official_web(cls, response):
        """提取豆瓣影视专题网站链接

        """
        return response.xpath(
            "//div[@id='info']/span[contains(text(), '官方小站')]/following::a/attribute::href"
        ).extract_first()
        


class Workers:
    """
    解析豆瓣影视页面中的演职人员信息
    可以得到内容的链接为 https://movie.douban.com/subject/{影视 ID}/celebrities
    * extract_basic, 解析影视演职人员基本信息，包括需要的中文信息和别名，以及豆瓣提供的 ID
    * extract_duties, 解析演职人员id 和对应的岗位

    Properties:
    -------------
    __worker: 演职人员基本信息，id 为演职人员 ID，name 为演职人员姓名，alias 为演职人员的
        非中文名称，url 为演职人员的详情页链接
    __worker_duty: 演职人员职责信息，sid 为当前影片的 ID，id 为演职人员 ID，duty 为演职人
        员岗位，action 为演员参与到影片的方式，role 为演员在影片中的角色姓名
    """
    __worker = namedtuple("worker", ["id", "name", "alias", "url"])
    __worker_duty = namedtuple("duty", ["sid", "id", "duty", "action", "role"])
    @classmethod
    def extract_basic(cls, response):
        """提取演职人员基本信息

        提取演职人员信息，根据 generator 判断是否需要以生成器的方式抛出结果

        Results:
        ---------
        result: list, 以元组形式保存了 id、姓名(中文注解的姓名)、其他别名、头像图片
        """
        elements = response.css(\
            "div.article > div#celebrities > div.list-wrapper > ul")
        

        for element in elements:
            ids = [i.strip() for i in element.css("li > a:first-child::attr(href)").re("\d{2,}")]
            names = [i.strip() for i in element \
                        .css("li > a:first-child::attr(title)").extract()]
            urls = element.css("li > a:first-child > div::attr(style)").re("\((https?.+?)\)")
            for id, name, url in zip(ids, names, urls):
                # 假设了姓名中有中文存在，才有可能有其他语言的姓名，否则就只有一个姓名
                if re.search(r"[\u2E80-\uFAFF]+", name):
                    if len(name.split(" ")) > 1:
                        name, alias = name.split(" ", 1)
                    else:
                        alias = None
                else:
                    alias = None
    
                yield cls.__worker(id=id, name=name, alias=alias, url=url)
            

    @classmethod
    def extract_duties(cls, response):
        """获取岗位信息

        获取演职人员岗位信息，生成一个元组信息: 影视 ID、演职人员 ID、岗位、动作类型(主要为演
        员参与的动作，eg: 配音、饰演)、角色姓名。以生成器的方式得
        传输结果
        """
        product_id = re.search(r"/(\d{3,})/?", response.url).group(1)
        duties = response.css(
                "div.article > div#celebrities > div.list-wrapper > h2::text"
            ).extract()
        elements = response.css(\
            "div.article > div#celebrities > div.list-wrapper > ul")
        for duty, element in zip(duties, elements):
            ids = [i.strip() for i in element.css("li > a:first-child::attr(href)").re("\d{2,}")] 
            roles = [i.split(" ", 1)[-1] for i in element.css("li > div.info > span.role::text").re("\((.*)\)")]
            actions = [i.split(" ", 1)[0] for i in element.css("li > div.info > span.role::text").re("\((.*)\)")]
            duty = "/".join(i.strip() for i in duty.split(" ", 1))

            if roles and actions:
                for id, role, action in zip(ids, roles, actions):
                    yield cls.__worker_duty(sid=product_id, id=id, duty=duty, \
                        action=action, role=role)
            else:
                for id in ids:
                    yield cls.__worker_duty(sid=product_id, id=id, duty=duty, \
                        action=None, role=None)


class Pictures:
    """
    解析海报页面图片链接: https://movie.douban.com/subject/<影视 ID>/photos?type=R
    解析壁纸页面图片链接: https://movie.douban.com/subject/<影视 ID>/photos?type=W

    # * extract_poster, 提取海报信息
    # * extract_wallpaper, 提取壁纸信息

    Properties:
    -------------
    __poster: 海报信息, id 为海报的 ID，url 为海报的链接，description 为海报的描述信息，
        可能包括一些使用区域等描述，specification 为海报的规格信息
    __wallpaper: 壁纸信息，id 为壁纸的 ID，url 为壁纸的链接，specification 为壁纸规格信息
    """
    __poster = namedtuple("poster", ["id", "url", "description", "specification"])
    __wallpaper = namedtuple("wallpaper", ["id", "url", "specification"])
    @classmethod
    def extract_poster(cls, response):
        """
        提取海报链接

        保存了当前图片列表页中的链接，没有请求原始海报（需要解决登录的问题），保存的内容为图片
        ID、链接、海报简短描述（一般是描述的是使用场景）、原始海报规格(注意不是保存的链接图片的
        规格)

        Results:
        ------------
        result: dict, key 是海报的 id，nametuple 保存 value，包括了 id,url, 
            description, specification
        next_: boolean 或者 str，返回下一页 URL，如果没有下一页那么返回 False
        """
        elements = response.css("div#wrapper > div#content div.article > ul > li")

        if elements:
            result = {}
            for element in elements:
                id = element.css("::attr(data-id)").extract_first().strip()
                url = element.css("div.cover img::attr(src)").extract_first().strip()
                description = element.css("div.name::text").extract_first().strip()
                specification = element.css("div.prop::text").extract_first().strip()
                result[id] = cls.__poster(id, url, description, specification)

            # 如果有下一页需要和结果一起传出
            has_next = response.css(
                "div#wrapper div.article > div.paginator > span.next > a::attr(href)"
                ).extract_first()
            if has_next:
                next_ = has_next.strip()
            else:
                next_ = False
            
            return result, next_


    @classmethod
    def extract_wallpaper(cls, response):
        """
        提取壁纸链接

        保存了当前图片列表页中的链接，没有请求原始壁纸（需要解决登录的问题），保存的内容为图片
        ID、链接、原始海报规格(注意不是保存的链接图片的规格)

        Results:
        ------------
        result: dict, key 是海报的 id，nametuple 保存 value，包括了 id,url, 
           specification
        next_: boolean 或者 str，返回下一页 URL，如果没有下一页那么返回 False
        """    
        elements = response.css("div#wrapper > div#content div.article > ul > li")

        if elements:
            result = {}
            for element in elements:
                id = element.css("::attr(data-id)").extract_first().strip()
                url = element.css("div.cover img::attr(src)").extract_first().strip()
                
                specification = element.css("div.prop::text").extract_first().strip()
                result[id] = cls.__wallpaper(id, url, specification)

            # 如果有下一页需要和结果一起传出
            has_next = response.css(
                "div#wrapper div.article > div.paginator > span.next > a::attr(href)"
                ).extract_first()
            if has_next:
                next_ = has_next.strip()
            else:
                next_ = False
            
            return result, next_ 


class Comments:
    """
    提取评论信息
    解析短评论信息，短评论有分为看过短片和没有看过影片的链接:
    * 看过影片的链接：https://movie.douban.com/subject/<影视 ID>/comments?status=P
    * 没有看过的链接：https://movie.douban.com/subject/<影视 ID>/comments?status=F

    解析长评论信息
    解析长评论信息，长评论链接：https://movie.douban.com/subject/<影视 ID>/reviews

    Properties:
    -------------
    __short: 影片短评，name 用户姓名，uid 用户链接，upic 用户头像，date 用户评论日期
        cid 用户评论 ID，content 用户评论的内容，thumb 赞同该评论用户，watched 用户是否已
        经观看-因为影片的评论包括了想看和已看两种类型
    __review: 影片评论，针对影片发表长评论。name 用户姓名，uid 用户链接，upic 用户头像，
        date 用户评论日期，cid 用户评论 ID，short_content 用户评论的部分内容（完整内容需要
        请求其他页面），title 评论标题，contetn_url 可以获取到详细评论的 URL，thumb 赞同
        该评论的数量，down 不赞同该评论的数量，reply 回复该评论的数量
    """
    __short = namedtuple("short_comment", \
        ["name", "uid", "upic", "date", "cid", "rate", "content", "thumb", "watched"])

    __review = namedtuple("review", \
        ["name", "uid", "upic", "date", "cid", "rate", "short_content", "title", \
            "content_url", "thumb", "down", "reply"])
    @classmethod
    def extract_short_comment(cls, response):
        """
        提取短评论信息

        获取到的信息包括用户姓名(name), 用户 ID(uid), 用户头像链接(upic), 
        用户评论日期(date), 用户评论的 ID(cid, 豆瓣页面获取), 用户评分(rate，保留 5 星评
        等级), 用户评论内容(content), 其他用户支持的数量(thumb), 用户是否已经看过(watched)

        Results:
        ------------
        result: dict, key 是评论的 id，nametuple 保存 value，包括了 name, uid, upic,
            date, cid, rate, content, thumb
        next_: boolean 或者 str，返回下一页 URL，如果没有下一页那么返回 False
        """
        elements = response.css(
            "div#wrapper > div#content  div.article div#comments > div.comment-item"
        )

        if elements:
            result = {}
            # 判断用户是否已经看过影片需要从页面链接中 status 值判断
            if re.search("status=(\w)", response.url).group(1) == "F":
                watched = False 
            elif re.search("status=(\w)", response.url).group(1) == "P":
                watched = True
            else:
                raise ValueConsistenceError(f"can't extract watched information")

            for element in elements:
                name = element.css("div.avatar > a::attr(title)") \
                        .extract_first().strip() 
                uid = element.css("div.avatar > a::attr(href)") \
                        .extract_first().strip()
                upic = element.css("div.avatar > a > img::attr(src)") \
                        .extract_first().strip()
                date = element.css(
                        "div.comment span.comment-info > span.comment-time::attr(title)"
                    ).extract_first().strip()
                cid = element.css("::attr(data-cid)").extract_first().strip()
                rate = element.css(
                        "div.comment  span.comment-info > span.rating::attr(class)"
                    ).re("\d+")
                
                # 如果没有评分值，则返回 None
                rate = None if not rate else int(float(rate[0].strip())) // 10
                content = element.css("div.comment > p span.short::text") \
                        .extract_first().strip()
                thumb = int(float(element.css("div.comment > h3  span.votes::text") \
                        .extract_first().strip()))
                

                result[cid] = cls.__short(name=name, uid=uid, upic=upic, watched=\
                    watched, date=date, cid=cid, rate=rate, content=content, thumb=thumb)
            # 如果有下一页需要和结果一起传出
            has_next = response.css(
                "div#wrapper div.article div#comments > div#paginator > a.next::attr(href)"
                ).extract_first()

            if has_next:
                next_ = re.sub("^(.*comments).*$", 
                    lambda x: x.group(1) + has_next.strip(), response.url)
            else:
                next_ = False
            
            return result, next_  


    @classmethod
    def extract_reviews(cls, response):
        """
        提取长评论信息

        获取到的信息包括用户姓名(name), 用户 ID(uid), 用户头像链接(upic), 
        用户评论日期(date), 用户评论的 ID(cid, 豆瓣页面获取), 用户评分(rate，保留 5 星评
        等级), 用户评论短内容(short_content，保留了显示内容), 用户评论完整内容可以请求的 
        URL (content_url) 其他用户支持的数量(thumb), 不支持的数量(down)，恢复数量(reply)

        Results:
        ------------
        result: dict, key 是评论的 id，nametuple 保存 value，包括了 name, uid, upic,
            date, cid, rate, content, thumb
        next_: boolean 或者 str，返回下一页 URL，如果没有下一页那么返回 False
        """
        elements = response.css("div.review-list > div")

        if elements:
            result = {}
            for element in elements:
                name = element.css("header.main-hd > a.name::text") \
                    .extract_first().strip()
                uid = element.css("header.main-hd > a.name::attr(href)") \
                    .extract_first().strip() 

                upic = element.css("header.main-hd > a.avator > img::attr(src)") \
                    .extract_first().strip()

                date = element.css("header.main-hd > span.main-meta::text") \
                    .extract_first().strip()
                
                cid = element.css("::attr(data-cid)") \
                    .extract_first().strip()
                
                rate = element.css(
                        "header.main-hd > span.main-title-rating::attr(class)"
                    ).re("\d+")
        
                # 如果没有评分值，则返回 None
                rate = None if not rate else int(float(rate[0].strip())) // 10

                short_content = "".join(i.strip() for i in element.css(
                        "div.main-bd > div.review-short > div.short-content::text"
                    ).extract())

                title = element.css("div.main-bd > h2 > a::text").extract_first().strip()
                content_url = element.css("div.main-bd > h2 > a::attr(href)") \
                    .extract_first().strip()
                
                thumb = element.css("div.main-bd > div.action a[title='有用'] > span::text") \
                    .extract_first().strip()

                thumb = 0 if not thumb else int(float(thumb.strip()))

                down = element.css("div.main-bd > div.action a[title='没用'] > span::text") \
                    .extract_first().strip()

                down = 0 if not down else int(float(down.strip()))

                reply = element.css("div.main-bd > div.action a.reply::text").re("\d+")

                reply = 0 if not reply else int(float(reply[0].strip()))

                result[cid] = cls.__review(name=name, uid=uid, upic=upic, \
                    date=date, cid=cid, rate=rate, short_content=short_content,
                    title=title, content_url=content_url, thumb=thumb, down=down,
                    reply=reply)

                        # 如果有下一页需要和结果一起传出
            has_next = response.css(
                "div#wrapper div#content div.article > div.paginator > span.next >a::attr(href)"
                ).extract_first()

            if has_next:
                next_ = re.sub("^(.*reviews).*$", 
                    lambda x: x.group(1) + has_next.strip(), response.url)
            else:
                next_ = False
            
            return result, next_  


    @classmethod
    def extract_review_content(cls, response):
        """
        解析影评评论中的完成内容

        页面的请求于 extract_reviews 中的 content_url
        """
        contents = response.css("div#link-report > div.review-content::text") \
            .extract()
        
        if contents:
            return "\n".join(content.strip() for content in contents)
        else:
            raise ValueConsistenceError(f"can't get review: {response.url}")



class People:
    """解析演职人员 Profile

    解析演职人员的具体信息，解析信息的链接:
    https://movie.douban.com/celebrity/<演职人员 id>/

    Methods:
    -----------
    * extract_bio_informaton: 获取演职人员相关信息
    * extract_text: 辅助方法，利用 xpath 的判断元素中文本是否为对应的之值，在获取其兄弟文本内容
        是一个静态方法


    Properties:
    -----------
    __bio: 演职人员具体的信息，直接获取演职人员页面信息，包括
        * id 豆瓣数据中的 id
        * name 姓名，豆瓣标题显示姓名
        * gender 性别
        * constellation 星座
        * birthdate 出生日期
        * birthplace 出生地
        * profession 职业
        * alias 其他姓名
        * alias_cn 其他中文姓名（翻译）
        * family 家庭成员
        * imdb_link IMBD 数据中的链接
        * official_web 官方网站
        * introduction 简介
    """
    __bio = namedtuple("bio", \
        ["id", "name", "gender", "constellation", "birthdate", "birthplace", "profession", \
            "alias", "alias_cn", "family", "imdb_link", "official_web", "introduction"])
    
    @classmethod
    def extract_bio_informaton(cls, response):
        """解析基本的信息

        从演职人员页面中得到进行解析，得到如下数据：
            * id 豆瓣数据中的 id
            * name 姓名，豆瓣标题显示姓名
            * gender 性别
            * constellation 星座
            * birthdate 出生日期
            * birthplace 出生地
            * profession 职业
            * alias 其他姓名
            * alias_cn 其他中文姓名（翻译）
            * family 家庭成员
            * imdb_link IMBD 数据中的链接
            * official_web 官方网站
            * introduction 简介
        """
        id_ = re.search("celebrity\/(\d{2,})\/", response.url).group(1)
        
        name = response.css("head > title::text") \
                        .extract_first().replace("(豆瓣)", "") \
                        .strip()
    
        gender = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='性别']/following-sibling::text()")

        constellation = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='星座']/following-sibling::text()")

        birthdate = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='出生日期']/following-sibling::text()")

        birthplace = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='出生地']/following-sibling::text()")
        
        profession = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='职业']/following-sibling::text()")

        alias = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='更多外文名']/following-sibling::text()")

        alias_cn = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='更多中文名']/following-sibling::text()")

        family = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='家庭成员']/following-sibling::text()")

        imdb_link = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='imdb编号']/following-sibling::text()")
        
        official_web = cls.extract_text(response, sub_option=": ", \
            query="//span[text()='官方网站']/following-sibling::text()")

        # 解析任务简介
        element = response.css("div.article div#intro > div.bd > span.all::text").extract()
        
        if element:
            introduction = "\n".join(i.strip() for i in element)
        else:
            introduction = response.css("div.article div#intro > div.bd::text") \
                .extract_first()
            # 解析到数据之后删除多余字符
            if introduction.strip():
                introduction = introduction.strip()
            else:
                introduction = None
            
        return cls.__bio(name=name, gender=gender, constellation=constellation, \
            birthdate=birthdate, birthplace=birthplace, profession=profession, \
            alias=alias, alias_cn=alias_cn, family=family, imdb_link=imdb_link, \
                official_web=official_web, introduction=introduction, id=id_)


    @staticmethod
    def extract_text(response, query, sub_option=None):
        """提取指定 Tag 中的值

        从 response 中获取到响应的值，如果找到了相关的值，再利用 sub_option 中的值去删除相关
        字符。为了保证简洁性，使用 xpath 作为 query

        Args:
        ---------
        response: URL 响应的页面
        query: str, xpath 查询语句
        sub_option: str, regex 的表达式
        """
        text = response.xpath(query).extract_first()
        
        if text:
            if sub_option is None:
                text = text.strip().replace(" / ", "/")
            else:
                text = re.sub(sub_option, "", text).strip().replace(" / ", "/")

        return text



class Awards:
    """影视获奖信息

    解析演职人员的具体信息，解析信息的链接:
    https://movie.douban.com/subject/<影视 ID>/awards/

    Methods:
    -----------
    * extract_awards: 获取影视获奖信息

    Properties:
    -----------
    __award: 演职人员具体的信息，直接获取演职人员页面信息，包括
        * host 颁奖主办方
        * year 获奖年份
        * name 奖项类型名称
        * person 获奖人姓名
        * status 最终获奖状态, 1 为获奖，0 表示只有提名
    """
    __award = namedtuple("award", \
        ["host", "year", "name", "person", "status"])

    @classmethod
    def extract_awards(cls, response):
        result = []

        for element in response.css("div.article > div.awards"):
            host = element.css("div.hd a::text").extract_first()
            year = element.css("div.hd >h2 > span::text").re("\d+")[0]
            
            names = element.css("ul.award > li:first-of-type::text").extract()

            # 姓名列表
            people_list = element.css("ul.award > li:nth-of-type(2)")
            # 需要判断是否有获奖人员信息，如果有信息需要解析出姓名和 ID
            for name, lis in zip(names, people_list):
                status = 0 if "(提名)" in name else 1
                if lis.css("a::text"):
                    urls = lis.css("a::attr(href)").extract()
                    persons = lis.css("a::text").extract()
                    for url, person in zip(urls, persons):
                        result.append(
                            cls.__award(host=host, year=year, name=name, \
                                status=status, person=json.dumps(
                                {"id": re.search("celebrity/(\d+)", url).group(1), "name":person},
                                ensure_ascii=False))
                        )
                # 没有人员信息
                else:
                    result.append(
                        cls.__award(host=host, year=year, name=name, \
                            status=status, person=None)
                    )
        return result