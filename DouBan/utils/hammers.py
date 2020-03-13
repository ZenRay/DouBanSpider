#-*-coding:utf8-*-
"""
The script is a addictive tool that can deal with some special task:
1. extract the first PinYin character
"""

from __future__ import absolute_import

import re
from pypinyin import Style, pinyin


__all__ = ["extract1st_char"]


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