#-coding:utf8-*-
"""
Compress or convert information, convert list as json data:

"""
from __future__ import absolute_import


import json


from DouBan.utils.exceptions import LostArgument

__all__ = ["compress2json"]


def compress2json(keys, values):
    """Mapping Data And Convert To JSON

    There are two types mapping: 1VS.1 or 1VS.more. 1VS.1 type is each key has 
    one value, example:
    >>> keys = ['格蕾塔·葛韦格', '西尔莎·罗南', '艾玛·沃森', '佛罗伦斯·珀', '伊莱扎·斯坎伦', '劳拉·邓恩']
    >>> values = ['导演', '饰 Jo March', '饰 Meg March', '饰 Amy March', '饰 Beth March', '饰 Marmee March']
    >>> compress2json(keys, values)
        '{"格蕾塔·葛韦格": "导演", "西尔莎·罗南": "饰 Jo March", "艾玛·沃森": "饰 Meg March", "佛罗伦斯·珀": "饰 Amy March", "伊莱扎·斯坎伦": "饰 Beth March", "劳拉·邓恩": "饰 Marmee March"}'

    If the 1VS.more type, each key mapping to multi values--it's sequence value:
    >>> comment = ['非常好地还原了书里的内容。弟弟问爸爸智英姐姐喜欢吃什么，爸爸说红豆面包。弟弟买了一袋红豆面包给姐姐送去之后，姐姐说：红豆面包？',
                    '没想到，看到智英变为外婆和母亲对话，眼泪就下来了。东亚三国手牵手，谁先平权谁是狗。',
                    '选角失败，世界上并没有孔刘这种完美老公。',
                    '愿每一位女性都能以一个独立的人格存在并且可以获得尊重',
                    '82年生的金智英有体贴的老公，有亲人的关爱，然而依然过得很抑郁，因为她面对的是男尊女卑的社会，琐碎但理直气壮的日常伤害。']
    >>> vote = ['4767', '2618', '2395', '2400', '800']
    >>> comment_author = ['成语', '既挽', '曹屎蛋', '糖醋金瓜', '同志亦凡人中文站']
    >>> compress2json(["author", "vote", "comment"], [comment_author, vote, comment])
    """
    data = {}
    # if values length is one, use key: value, otherwise use: key: [value1, value2...]
    if len(values) == 0:
        raise LostArgument("Missing values, there is only keys")
    # check inverse method, if first index value is mot sequnce, it must be a 
    # single sequence 
    elif not isinstance(values[0], (list, tuple)):
        for key, value in zip(keys, values):
            data[key] = value
    else:
        for index, key in enumerate(keys):
            data[key] = values[index]

    return json.dumps(data, ensure_ascii=False)
