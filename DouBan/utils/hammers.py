#-*-coding:utf8-*-
"""
The script is a addictive tool that can deal with some special task:
1. extract the first PinYin character
"""

from __future__ import absolute_import

from pypinyin import Style, pinyin

import urllib3
from requests import exceptions

__all__ = ["extract1st_char", "_url_valid"]


def extract1st_char(string):
    """Extract First Accent character

    Extract the first chinese word accent character, but keep another character.
    
    Examples:
    >>> string = "逃离比勒陀利亚 逃离比勒陀利亚 7.5"
    >>> extract1st_char(string)
        'tlbltlytlbltly7.5'
    """
    string = string.replace(" ", "")
    result = pinyin(string, style=Style.INITIALS, errors="default", strict=False)
    
    return "".join(i[0] for i in result).lower()



def _url_valid(url):
    """检查 URL 是否有效
    
    URL 有效性检验参考了 requests 模块 models 检验的代码
    """
    # Support for unicode domain names and paths.
    try:
        scheme, auth, host, port, path, query, fragment = urllib3.util.parse_url(url)
    except exceptions.LocationParseError as e:
        raise exceptions.InvalidURL(*e.args)

    if not scheme:
        error = ("Invalid URL {0!r}: No schema supplied. Perhaps you meant http://{0}?")
        error = error.format(url)

        raise exceptions.MissingSchema(error)

    if not host:
        raise exceptions.InvalidURL("Invalid URL %r: No host supplied" % url)

    # In general, we want to try IDNA encoding the hostname if the string contains
    # non-ASCII characters. This allows users to automatically get the correct IDNA
    # behaviour. For strings containing only ASCII characters, we need to also verify
    # it doesn't start with a wildcard (*), before allowing the unencoded hostname.
    if not host:
        raise exceptions.InvalidURL('URL has an invalid label.')
    elif host.startswith('*'):
        raise exceptions.InvalidURL('URL has an invalid label.')

    return True
