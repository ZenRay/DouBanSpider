#coding:utf8
from __future__ import absolute_import
import re
import json
import datetime

from collections import namedtuple
from DouBan.utils.exceptions import LostArgument, ValueConsistenceError


class Details:
    """
    豆瓣影视内容详情页解析，主要功能是解决 Scrapy 得到 response 之后进行页面解析，得到相应的结果:
    * extract_title, 提取影视标题
    * extract_rate, 提取影视评分
    * extract_rate_collections, 提取影视评分人数
    * extract_cover_url, 提取影视详情页的海报链接
    * extract_category, 提取类型信息
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
    ------如果页面没有演职人员链接时，需要从主页提取相关信息----------
    * extract_directors, 提取导演信息
    * extract_screenwriter, 提取编剧信息
    * extract_actors, 提取演员信息
    """
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
            result = {"title": title, "alias": None}
        else:
            # 需要确认 origin_title 是否在提取到的标题中，如果不存在则发生值不一致异常
            if origin_title not in title:
                raise ValueConsistenceError(
                f"`title` isn't consistent with `origin_title`. Response URL: {response.url}"
                )
            result = {
                "title": origin_title, 
                "alias": title.replace(origin_title, "").strip()
            }
        
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
    def extract_category(cls, response):
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
        ).extract_first().strip()
        
        return  result.replace(" / ", "/")


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
            if country.group() in result:
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
                result += "/" + additional.replace(" / ", "/")

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
        if Details.check_attribute(response, name="导演", \
            query="div#info > span:nth-of-type(1) > span::text"):
            result = {}

            # 遍历导演以及豆瓣导演 ID
            names = response.css(
                    "div#info > span:nth-of-type(1) > span.attrs > a::text"
                ).extract()
            ids_  = response.css(
                    "div#info > span:nth-of-type(1) > span.attrs > a::attr(href)"
                ).extract()
            for name, id_ in zip(names, ids_):
                id_ = None if "search_text" in id_ else re.search(r"\d+", id_).group().strip()
                result[name.strip()] = id_

            return result


    @classmethod
    def extract_screenwriter(cls, response):
        """提取页面的编剧信息
        """
        # 如果类型是编剧存在，再查询编剧信息
        if Details.check_attribute(response, name="编剧", \
            query="div#info > span:nth-of-type(2) > span::text"):
            result = {}

            names = response.css(
                    "div#info > span:nth-of-type(2) > span.attrs > a::text"
                ).extract()

            ids_ = response.css(
                    "div#info > span:nth-of-type(2) > span.attrs > a::attr(href)"
                ).extract()
            for name, id_ in zip(names, ids_):
                id_ = None if "search_text" in id_ else re.search(r"\d+", id_).group().strip()
                result[name.strip()] = id_

            return result


    @classmethod
    def extract_actors(cls, response):
        """提取演员信息
        """
        # 如果类型是编剧存在，再查询编剧信息
        if Details.check_attribute(response, name="主演", \
            query="div#info > span:nth-of-type(3) > span::text"):
            result = {}

            names = response.css(
                    "div#info > span:nth-of-type(3) > span.attrs > a::text"
                ).extract()

            ids = response.css(
                    "div#info > span:nth-of-type(3) > span.attrs > a::attr(href)"
                ).extract()

            for name, id_ in zip(names, ids):
                id_ = None if "search_text" in id_ else re.search(r"\/(\d{2,})\/", id_).group(1).strip()
                result[name.strip()] =  id_

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
    def extract_cover_url(cls, response):
        """提取详情页海报链接
        """
        return response.css(
                "div#mainpic > a > img[title='点击看更多海报']::attr(src)"
            ).extract_first().strip()


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


class Workers:
    """
    解析豆瓣影视页面中的演职人员信息
    可以得到内容的链接为 https://movie.douban.com/subject/{影视 ID}/celebrities
    * extract_basic, 解析影视演职人员基本信息，包括需要的中文信息和别名，以及豆瓣提供的 ID
    * extract_duties, 解析演职人员id 和对应的岗位
    """
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
    
                yield id, name, alias, url
            

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
                    yield product_id, id, duty, action, role
            else:
                for id in ids:
                    yield product_id, id, duty, None, None


class Pictures:
    """
    解析海报页面图片链接: https://movie.douban.com/subject/<影视 ID>/photos?type=R
    解析壁纸页面图片链接: https://movie.douban.com/subject/<影视 ID>/photos?type=W

    # * extract_poster, 提取海报信息
    # * extract_wallpaper, 提取壁纸信息
    """
    __poster = namedtuple("poster", ["id", "url", "description", "specification"])
    __wallpaper = namedtuple("wallpaper", ["id", "url", "specification"])
    __slots__ = ()
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


