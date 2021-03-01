import requests
import execjs
import re


from os import path


from ..exceptions import InappropriateArgument
from ..hammers import _url_valid

# 导入js
_current = path.dirname(__file__)
_encrypt_file = path.join(_current, "./libs/decrypt.js")

if not path.exists(_encrypt_file):
    raise FileNotFoundError("解密使用 JavaScript 文件未找到")

with open(_encrypt_file, 'r', encoding='utf-8', errors='ignore') as file:
    js = file.read()
    ctx = execjs.compile(js)


class Decrypt:
    """
    解密豆瓣响应数据

    提供了两种类方法处理数据，以及一种对象调用方式处理数据，得到的结果都是解密数据:

    Methods:
    -----------
    request: 以 URL 方式请求数据解析，默认使用 'GET' 方法，其他请求需要参数以关键字方式调用
    _decrypt: 对获取到的响应对象，进行解密处理。处理对方式是调用 JS 方法
    
    """
    def request(self, url, *, method="GET", **kwargs):
        """对 URL 响应结果解密

        传入需要解密的页面 URL 以及页面请求需要的参数
        """
        response = requests.request(method=method, url=url, **kwargs)
        return self._decrypt(response)


    def _decrypt(self, response):
        """解密获取到的页面响应结果

        对请求到的响应页面进行解密
        """
        # 需要解密的部分数据
        text = re.search('window.__DATA__ = "([^"]+)"', response.text).group(1)
        data = ctx.call('decrypt', text)
        return data

 
    def __call__(self, *args, **kwargs):
        # 位置参数数量不正确，说明传入的参数不正确：位置参数只能是 response 或者 URL
        if len(args) != 1:
            raise InappropriateArgument("传输的位置参数数量不正确，只需要一个位置参数")
        
        # 位置参数是网页请求响应
        if isinstance(args[0], requests.Response):
            return self._decrypt(args[0])
        
        # 位置参数是 URL
        elif _url_valid(args[0]):
            return self.request(args[0], **kwargs)
        else:
            raise InappropriateArgument(f"解密仅能针对页面响应结果或者 URL，获取参数为:{args[0]}")