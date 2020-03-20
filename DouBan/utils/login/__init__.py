#-*-coding:utf8-*-
from __future__ import absolute_import
import requests
import json

from os import path

from ._settings import payload, headers, redis_conf
from ..exceptions import InappropriateArgument


douban_url = "https://accounts.douban.com/j/mobile/login/basic"


def extract_info(filepath=None, sep=" "):
    """Extract Username And Password

    Extract username and password in a specific file with a specific delimiter.

    Arguments:
        filepath: file path, it's a user and password
        sep: delimiter, use a special delimiter
    """
    if filepath is None:
        filepath = path.join(path.dirname(__file__), "user_pw.txt")

    with open(filepath, "r") as file:
        file.readline()
        for line in file.readlines():
            data = line.split(sep)
            user = data[0]
            passwd = data[1]
            yield {"name": user, "passwd": passwd}


def generate_cookie(name, passwd, url=None, target="douban"):
    if url is None:
        if target.lower() == "douban":
            url = douban_url
        else:
            raise InappropriateArgument("Missing URL address, must get url or target!")

    with requests.session() as session:
        payload["name"] = name
        payload["password"] = passwd
        response = session.post(url, data=payload, headers=headers)
        if response.json()["status"] == "success":
            cookies = session.cookies.get_dict()
            return cookies
        else:
            raise ConnectionError("Can't login web")


def douban_cookie(filepath=None):
    if filepath is None:
        filepath = path.join(path.dirname(__file__), "user_pw.txt")
        
    for item in extract_info(filepath):
        yield generate_cookie(**item)


if __name__ == "__main__":
    mv_headers = headers.copy()
    del mv_headers["Origin"]
    del mv_headers["Referer"]
    mv_headers["Host"] = "movie.douban.com"

    filepath = path.join(path.dirname(__file__), "user_pw.txt")
    cookies = []
    for item in extract_info(filepath):
        cookie = generate_cookie(**item)
        cookies.append(cookie)
    print(cookies)
