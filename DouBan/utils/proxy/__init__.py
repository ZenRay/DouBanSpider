#coding:utf8
from __future__ import absolute_import
import hashlib
import requests
import time
from .conf import configure

QUANTITY_PROXY_LICENSE = configure.parser.get("abuyun", "QUANTITY_PROXY_LICENSE")
QUANTITY_PROXY_SECRET = configure.parser.get("abuyun", "QUANTITY_PROXY_SECRET")



def request_abuyun(cnt, secret=QUANTITY_PROXY_SECRET, license_proxy=QUANTITY_PROXY_LICENSE):
    secret = secret
    params = {
        "license": license_proxy,
        "time": int(time.time()),
        "cnt": cnt,
    }
    params["sign"] = hashlib.md5((params["license"] + str(params["time"]) + secret).encode('utf-8')).hexdigest()
    try:
        response = requests.get(
            url="https://api-ip.abuyun.com/obtain",
            params=params,
            headers={
                "Content-Type": "text/plain; charset=utf-8",
            },
            data="1"
        )
        result = response.json()
    except requests.exceptions.RequestException:
        result = False
        
    return result


__all__ = ["configure", "request_abuyun"]