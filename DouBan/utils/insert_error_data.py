#-*-coding:utf8-*-
"""
Insert data by hand. Because the data can't insert data in pipeline
"""
from __future__ import absolute_import

import copy
import os
import pandas as pd
import numpy as np
import logging
import logging.config
import json

from DouBan.settings import DATABASE_CONF, TABLE_FIELDS, LOG_ENABLED, LOG_FILE, LOG_LEVEL
from DouBan.utils.base import BaseSQLPipeline
from DouBan.utils.hammers import extract1st_char



LOG_FILE = LOG_FILE.replace(".log", "_insert_error.log")


LOG_CONFIG = {
    "version": 1,
    'formatters': {
        'brief': {
            'format': '%(asctime)s - %(name)s - %(message)s',
            "datefmt": "%Y/%m/%d %H:%M:%S"
        },
        "detail": {
            "format": '%(asctime)s [%(module)s - %(funcName)s] %(levelname)s: %(message)s',
            "datefmt": "%Y/%m/%d %H:%M:%S"
        }
    },
    'handlers': {
        'console': {
            "class" : "logging.StreamHandler",
            "formatter": "brief",
            "level"   : "INFO",
            "stream"  : "ext://sys.stdout",
        },
        'file': {
            "class" : "logging.FileHandler",
            "formatter": "detail",
            "level": "INFO",
            "filename": LOG_FILE,
        },
        "detail_console": {
            "class" : "logging.StreamHandler",
            "formatter": "detail",
            "level"   : "INFO",
            "stream"  : "ext://sys.stdout",
        }
    },
    'loggers':{
        'StreamLogger': {
            'handlers': ['detail_console'],
            'level': 'DEBUG',
        },
        'FileLogger': {
            'handlers': ['file'],
            'level': 'DEBUG',
        }
    },
    # "root":{
    #     "level": "INFO",
    #     "handlers": ["console"]
    # }
}


logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger("FileLogger")
# logger = logging.getLogger("StreamLogger")


class Dealer(BaseSQLPipeline):
    def __init__(self, config=None, fields_mapping=None):
        if config is None:
            config = copy.deepcopy(DATABASE_CONF)
        
        if fields_mapping is None:
            self.schema = copy.deepcopy(TABLE_FIELDS)
        else:
            self.schema = fields_mapping

        self.db_connection = super().create_connection(database_type="mysql", \
            basic_config=config["mysql"])
        
        # self.cache_connection = super().create_connection("redis", **config["redis"])
        self._file = open(os.path.join(os.getcwd(), "error.json"), "w")
    

    def get_data(self, func, filepath, **kwargs):
        dataframe = func(filepath, **kwargs)

        return dataframe

    
    def process_item(self, item):
        def insert(sentence, data, single_query=True, cursor=None, insert_step=None):
            """Insert Data Into Table"""
            try:
                # insert a single data
                if single_query:
                    cursor.execute(sentence, data)
                    self.db_connection.commit()
                # insert many data with executemany method
                else:
                    cursor.executemany(sentence, data)
                    self.db_connection.commit()
                
                logger.info(f"Insert data {item['id']} Success at step <{insert_step}>!")
            except Exception as err:
                if insert_step is not None:
                    msg = f"Insert data {item} at step <{insert_step}> Failed"
                else:
                    msg = f"Insert data {item} Failed"
                logger.critical(msg)


        self.db_connection.ping(reconnect=True)
        # check whether video is contained and insert data
        cursor = self.db_connection.cursor()
        query = cursor.execute("SELECT id FROM video WHERE `name` = %s ORDER BY create_time DESC;", \
            (item['title'],))
        video_id = cursor.fetchone()[0]
        if query == 0:
            video_sent = self.insert_sentence("video", self.schema["video"].keys())
            video_data = self.extract_data(self.schema["video"], item, jane_key="title")  
            video_data = [None if isinstance(i, np.float) and  np.isnan(i) else i for i in video_data]
            insert(video_sent, video_data, cursor=cursor, insert_step="video")
            # get id
            cursor.execute("SELECT id FROM video WHERE `name` = %s ORDER BY create_time DESC;", \
            (item['title'],))
            video_id = cursor.fetchone()[0]

            logger.info("Insert data into video successfully")
        else:
            logger.info(f"{item['id']} inserted in video")

        # store actor data into table, and query id
        query = cursor.execute("SELECT id FROM video_actor WHERE `video_id`= %s", (video_id))
        if query == 0:
            actor_sent = self.insert_sentence("video_actor", self.schema["video_actor"].keys())
            actors_data = self.extract_list(item["actors"], True, video_id)
            
            if len(actors_data) > 0:
                insert(actor_sent, actors_data, single_query=False, cursor=cursor, \
                    insert_step="video_actor")
            else:
                logger.info(f"{item['id']} doesn't contain actors")

        # store director data into table, and query id
        query = cursor.execute("SELECT id FROM video_director WHERE `video_id`= %s", (video_id,))
        if query == 0:
            director_sent = self.insert_sentence("video_director", self.schema["video_director"].keys())
            directors_data = self.extract_list(item["director"], True, video_id)

            if len(directors_data) > 0:
                insert(director_sent, directors_data, single_query=False, \
                    cursor=cursor, insert_step="video_director")
            else:
                logger.info(f"{item['id']} doesn't contain directors")

        else:
            logger.info(f"{item['id']} inserted in video_director")

        
        # store category data into table
        query = cursor.execute("SELECT id FROM video_type WHERE `video_id`= %s", (video_id,))
        if query == 0:
            category_sent = self.insert_sentence("video_type", self.schema["video_type"].keys())
            category_data = self.extract_list(item["category"], appendix=video_id)
            
            if len(category_data) > 0:
                insert(category_sent, category_data, single_query=False, \
                    cursor=cursor, insert_step="video_type")
            else:
                logger.debug(f"Data id: {item['id']} doesn't contain Category information!")
        else:
            logger.info(f"{item['id']} inserted in video_type")
        
        # store review data into table
        query = cursor.execute("SELECT id FROM video_review WHERE `video_id`= %s", (video_id,))
        if query == 0:
            review_sent = self.insert_sentence("video_review", self.schema["video_review"].keys())
            reviews = json.loads(item["short_comment"])

            review_data = [(video_id, index, time_, score, content)  \
                    for index, (time_, score, content) in enumerate(zip(
                        reviews["time"], reviews["rate"], reviews["comment"]))]
            # 有评论数据再插入
            if len(review_data) > 0:
                insert(review_sent, review_data, single_query=False, \
                    cursor=cursor, insert_step="video_review")
            else:
                logger.debug(f"Data id: {item['id']} has no short comment!")
        else:
            logger.info(f"{item['id']} inserted in video_reviews")


        # store video extension region
        """
        [(1, '中国大陆', '2019', '2020', '135分钟', 0),
        (1, '美国', '2019', '2019-12-25', '135分钟', 0)]
        """
        query = cursor.execute("SELECT id FROM video_extension_region WHERE `video_id`= %s", (video_id,))
        if query == 0:
            extension_region_sent = self.insert_sentence("video_extension_region", \
                                    self.schema["video_extension_region"].keys())

            regions = self.extract_list(item["play_location"])
            release_times = self.extract_list(item["play_year"])
            extension_region_data = []
            for region, time_ in zip(regions, release_times):
                extension_region_data.append((video_id, region, \
                                int(item["release_year"]), time_, item["play_duration"], 0))
            
            if len(extension_region_data) > 0:
                insert(extension_region_sent, extension_region_data, \
                    single_query=False, cursor=cursor, insert_step="video_extension_region")
            else:
                logger.debug(f"Data id: {item['id']} has no extension region information!")
        else:
            logger.info(f"{item['id']} inserted in video_extension_region")

        # store role information into table
        query = cursor.execute("SELECT id FROM video_character WHERE `video_id`= %s", (video_id,))
        if query == 0:
            character_role_sent = self.insert_sentence("video_character", \
                                self.schema["video_character"].keys())
            character_role_data = [(video_id, index, name, role, url) \
                                    for index, (name, role, url) in \
                            enumerate(zip(*json.loads(item["worker_detail"]).values()))]
            
            if len(character_role_data) >= 1:
                insert(character_role_sent, character_role_data, single_query=False, \
                    cursor=cursor, insert_step="video_character")
            else:
                logger.debug(f"Data id: {item['id']} has no character information!")
        else:
            logger.info(f"{item['id']} inserted in video_character")

        return query


    def extract_data(self, mapping, item, jane_key=None, append_data=None):
        """Extract Values From Mapping
        
        There are several data source: 
            1. get the data from item, field and item key are same
            2. extract some character, if field endswith `jane`, must specify the
                jane key
            3. extract the appendix data directly, if field is not same with item
                key, but `append_data` must contain the field
        otherwise, raise the Exception

        Arguments:
            mapping: dict, field maps with item key
            item: item data
            jane_key: extract alias value that is same with field. Default None,
                which is not jane field
            append_data: dict, it's appendix data
        """
        data = []
        for key, item_key in mapping.items():
            if item_key.endswith("jane"):
                data.append(extract1st_char(item[jane_key]))
            elif item_key in item:
                data.append(item[item_key])
            elif (append_data is not None) and (item_key in append_data):
                data.append(append_data[item_key])
            else:
                raise InappropriateArgument(f"Missing key {item_key} in " + 
                                            f"fields Mapping: {mapping}\n" + 
                                            f"jane_key: {jane_key}\n" + 
                                            f"append_data: {append_data}")
        return data

    
    def extract_list(self, text, jane=False, appendix=None, split_char="/"):
        """Extract List Data

        If there is split character `/`, split the data, which there are many data.
        
        Arguments:
            text: string text
            key: it is item key, specify the value being splited
            jane: if True, extract accent first character of the `key`
        
        Example:
        >>> text = "西尔莎·罗南 / 艾玛·沃森 / 佛罗伦斯·珀 / 伊莱扎·斯坎伦"
        >>> extract_list(text, False, "/")
            ['西尔莎·罗南', '艾玛·沃森', '佛罗伦斯·珀', '伊莱扎·斯坎伦']
        >>> extract_list(text, True, None,  "/")
            [('西尔莎·罗南', 'xsh·ln'),
            ('艾玛·沃森', 'm·ws'),
            ('佛罗伦斯·珀', 'flls·p'),
            ('伊莱扎·斯坎伦', 'ylzh·skl')]
        >>> extract_list(text, True, 1,  "/")
            [(1, '西尔莎·罗南', 'xsh·ln'),
            (1, '艾玛·沃森', 'm·ws'),
            (1, '佛罗伦斯·珀', 'flls·p'),
            (1, '伊莱扎·斯坎伦', 'ylzh·skl')]
        """
        if text is None:
            return None

        split_data = [i.strip() for i in text.split(split_char)]

        if jane:
            jane_data = [extract1st_char(i) for i in split_data]
            result = []
            for item, jane in zip(split_data, jane_data):
                if appendix is not None:
                    result.append((appendix, item, jane))
                else:
                    result.append((item, jane))
        else:
            result = [(appendix, item)  if appendix is not None else (item) \
                        for item in split_data]
        return result


    def insert(self, sentence, data, single_query=True, cursor=None):
        """Insert Data Into Table"""
        try:
            # insert a single data
            if single_query:
                cursor.execute(sentence, data)
                self.db_connection.commit()
            # insert many data with executemany method
            else:
                cursor.executemany(sentence, data)
                self.db_connection.commit()
        except Exception as err:
            print(f"insert Wrong: {err}")


    def close(self):
        self.db_connection.close()


if __name__ == "__main__":
    # from DouBan.utils.insert_error_data import * 

    dealer = Dealer()
    # logger = logging.getLogger("StreamLogger")
    data = dealer.get_data(pd.read_json, "./err.txt", lines=True)

    for _, row in data.iterrows():
        # import ipdb; ipdb.set_trace()
        item = row.to_dict()
        query = dealer.process_item(item)

    # close connection
    dealer.close()