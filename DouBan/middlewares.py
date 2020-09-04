# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import random
import logging
import base64
import urllib
from scrapy import signals

from DouBan.utils.login import *
from DouBan.utils.proxy import configure, request_abuyun


from scrapy import signals
from twisted.internet import defer
from twisted.internet.error import (
    TimeoutError, DNSLookupError, ConnectionRefusedError, ConnectionDone, 
    ConnectError, ConnectionLost, TCPTimedOutError
)
from scrapy.http import HtmlResponse
from twisted.web.client import ResponseFailed
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

class DoubanSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DoubanDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)



class UserAgentDownloaderMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]


    def process_request(self,request, spider):
        ua = random.choice(self.user_agents)
        self.logger.debug('使用User-Agent ' + ua)
        request.headers['User-Agent'] = ua


class ABuYunDynamicProxyMiddleware:
    """使用阿布云动态代理通道
    """
    def __init__(self):
        proxyUser = configure.parser.get("abuyun", "PROXY_USER")
        proxyPass = configure.parser.get("abuyun", "PROXY_PASS")

        # 单次请求代理数量
        self.proxyServer = configure.parser.get("abuyun", "PROXY_SERVER")
        self.proxyAuth = "Basic " + base64.urlsafe_b64encode(
            bytes((proxyUser + ":" + proxyPass), "ascii")
        ).decode("utf8")
        # import ipdb; ipdb.set_trace()

    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxyServer
        request.headers["Proxy-Authorization"] = self.proxyAuth
        spider.logger.debug(f"当前页面使用代理服务: {request.url}")
        
    
class ABuYunHighQuantityProxyMiddleware:
    """使用阿布云高质量代理服务
    """
    def __init__(self):
        # get proxies
        self.proxy_count = configure.parser.getint("abuyun", "PROXY_COUNT")
        data = request_abuyun(cnt=1)

        self.proxies = data["proxies"] if "proxy" in data else []

    def process_request(self, request, spider):
        if len(self.proxies) == 0:
            spider.logger.debug("代理数量消耗殆尽")

        # 随机选择一个代理
        proxy_selected = random.choice(self.proxies)
        proxy = "http://" + proxy_selected
        request.meta["proxy"] = proxy

        spider.logger.debug('Use Proxy: ' + proxy)


    def process_response(self, request, response, spider):
        """处理异常请求结果
        """
        if int(response.status) not in [200, 301, 302]:
            
            data = request_abuyun(cnt=self.proxy_count)

            proxy = data["proxies"]
            request.meta["proxy"] = random.choice(proxy)
            self.logger.debug("Use New Proxy: {}".format(proxy))
            return request
        return response


   

class ABuYunDynamicProxyRetryMiddleware(RetryMiddleware):
    """
    使用阿布云动态代理进行重试
    """
    # logger = logging.getLogger(__name__)
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            max_retry_times=settings.getint('RETRY_TIMES', 5),
        )
        
    def __init__(self, max_retry_times):
        proxyUser = configure.parser.get("abuyun", "PROXY_USER")
        proxyPass = configure.parser.get("abuyun", "PROXY_PASS")
        
        # 单次请求代理数量
        self.proxy_count = configure.parser.getint("abuyun", "PROXY_COUNT")
        self.proxyServer = configure.parser.get("abuyun", "PROXY_SERVER")
        self.proxyAuth = "Basic " + base64.urlsafe_b64encode(
            bytes((proxyUser + ":" + proxyPass), "ascii")).decode("utf8")
        self.max_retry_times = max_retry_times
        
        # 添加 priority_adjust 属性才能调整重试策略
        self.priority_adjust = max_retry_times


    def process_response(self, request, response, spider):
        # 需要判断请求 URL 是否正确
        exception_link = "https://sec.douban.com/b?r="
        if exception_link in request.url:
            url = request.url.replace(exception_link, "")
            url = urllib.parse.unquote(url)
            # 更新 URL
            request = request.replace(url=url)
            
            spider.logger.debug(f"触发安全机制，更换请求的 URL: {request.url}")
        
        exception_link = "https://movie.douban.com/b?r="
        if exception_link in request.url:
            url = request.url.replace(exception_link, "")
            url = urllib.parse.unquote(url)
            # 更新 URL
            request = request.replace(url=url)
            
            spider.logger.debug(f"触发安全机制，更换请求的 URL: {request.url}")
            
        if str(response.status).startswith("4"):
            request.meta["proxy"] = self.proxyServer

            request.headers["Proxy-Authorization"] = self.proxyAuth
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        elif str(response.status).startswith("3"):
            spider.logger.debug("Acticate Antispider")

            request.meta["proxy"] = self.proxyServer

            request.headers["Proxy-Authorization"] = self.proxyAuth
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response


    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            spider.logger.debug("Catch Exception: {}".format(exception))
            
            request.meta["proxy"] = self.proxyServer

            request.headers["Proxy-Authorization"] = self.proxyAuth
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider)
            




class RandomDelayMiddleware:
    """设置随机延迟时间
    
    """
    def __init__(self, delay):
        self.delay = delay

    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.get("RANDOM_DELAY", 4)
        if not isinstance(delay, int):
            raise ValueError("RANDOM_DELAY need a int")
        
        return cls(delay)

    def process_request(self, request, spider):
        delay = random.randint(1, self.delay)
        spider.logger.debug("{name} Delay: {time}s".format(
            name=spider.name, time=delay))
        time.sleep(delay)


class CookiesRetryDownloaderMidddleware(RetryMiddleware):
    def process_request(self, request, spider):
        cookies = random.choice(list(douban_cookie()))
        request.cookies = cookies
        # return request