#-*-coding:utf8-*-
headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Length": "82",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "accounts.douban.com",
    "Origin": "https://accounts.douban.com",
    "Referer": "https://accounts.douban.com/passport/login_popup?login_source=anony",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "X-Requested-With": "XMLHttpRequest",
}

# login  body
payload = {
        'ck': '',
        "name": "mk46yb7m@linshiyouxiang.net",
        "password": "hzjy789@!",
        'remember': 'false',
        'ticket': '',
    }


# redis pool connection config
redis_conf = {
    "host": "192.168.1.31",
    "port": 6379,
    "password": None,
    "max_connections": 16, # use to initial connection pool
}