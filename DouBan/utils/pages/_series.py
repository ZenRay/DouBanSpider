#coding:utf8
from __future__ import absolute_import
import re
import json
import datetime
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
    * extract_directors, 提取导演信息
    * extract_screenwriter, 提取编剧信息
    * extract_release_year, 提取成片年份
    * extract_release_date, 提取影片播放日期，存在不同地区播放日期差异
    * extract_play_duration, 提取影片播放时长，存在不同地区不同差异
    * extract_nick_name, 影视标题别名
    * extract_imdb_id, 提取 IMDB 的 ID
    * extract_plot, 提取影视剧情简介
    * extract_tags, 提取豆瓣成员标签
    * extract_recommendation_type, 提取豆瓣推荐的类型，解析的内容页面上提供的"好于"类型的信息
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
                result = {name.strip(): id_}

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
                result = {name.strip(): id_}

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


