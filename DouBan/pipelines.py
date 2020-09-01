# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
import copy
import logging
import json
import bson
import pymongo
from os import path
from scrapy.exceptions import DropItem

from DouBan.utils.base import BaseSQLPipeline, BasePipeline
from DouBan.utils.hammers import extract1st_char
from DouBan.items import (
    DouBanDetailItem, DouBanAwardItem, CoverImageItem, ListItem, DouBanWorkerItem,
    DouBanPeopleItem, DouBanPhotosItem, DouBanEpisodeItem, DouBanCommentsItemM
)
from DouBan.database.manager.datamodel import *
from DouBan.database.conf import configure
from DouBan.database.manager import DataBaseManipulater
from DouBan.utils.exceptions import InappropriateArgument

cur_path = path.dirname(__file__)
manipulater = DataBaseManipulater()
class DoubanStoragePipeline(BaseSQLPipeline):
    """Store Data Item Pipeline
    
    Store Douban data item pipeline, `basic_config` is used to connect a database
    server, which is determined by db_type. Besides, use Redis connect pool to 
    redis server that settle down in settings. `Schema` is tables with fields that 
    is mapping with item keys.
    """
    db_type = "mysql"
    
    def __init__(self, basic_config, redis_config, schema, **kwargs):
        self.basic_config = basic_config
        self.redis_config = redis_config
        self.schema = schema 
        self._options = kwargs


    @classmethod
    def from_crawler(cls, crawler):
        schema = crawler.settings["TABLE_FIELDS"]
        settings = crawler.settings["DATABASE_CONF"]

        basic_config = copy.deepcopy(settings[cls.db_type])
        # basic_config["database"] = settings[cls.db_type]["database"]
        redis_config = settings["redis"]
        

        return cls(
            basic_config=basic_config,
            redis_config=redis_config,
            schema=schema
        )


    def open_spider(self, spider):
        self.redis_pool = self.create_connection("redis", self.redis_config)
        self.db_connection = self.create_connection(self.db_type, self.basic_config, **self._options)

        self.db_cursor = self.db_connection.cursor()
        # store the exceptions data item
        self.error_file_store = open(path.join(cur_path, f"log/err_{spider.name}.txt"), "a")
        
        # Store all data
        self.file = open(path.join(cur_path, f"log/.all.txt"), "a")


    def process_item(self, item, spider):
        def insert(sentence, data, query_step=None, single_query=True):
            """Insert Data Into Table"""
            try:
                # insert a single data
                if single_query:
                    self.db_cursor.execute(sentence, data)
                    self.db_connection.commit()
                # insert many data with executemany method
                else:
                    self.db_cursor.executemany(sentence, data)
                    self.db_connection.commit()
                
                self.log(f"Insert data at {query_step} success", level=logging.INFO)
            except Exception as err:
                self.error_file_store.write(json.dumps(dict(item, query_step=query_step), ensure_ascii=False)+ "\n")
                self.log(f"Insert value error: {data}, because {err}, At insert step {query_step}", \
                        level=logging.ERROR)
        

        # if item is not DoubanDataItem object, just return item
        if not isinstance(item, DoubanDataItem):
            return item

        # use the item key as redis key, and check the data id exists
        redis_key = item.__class__.__name__
        if self.redis_pool.sismember(redis_key, item["id"]):
            raise DropItem(f"Duplicated DataItem {item['id']}-{item['title']}")
        else:
            self.redis_pool.sadd(redis_key, item["id"])

        # !important 写入所有数据到 file
        self.file.write(json.dumps(dict(item), ensure_ascii=False)+"\n")    

        # reconnect the database
        self.db_connection.ping(reconnect=True)

        # store video data into table, and query id
        try:
            video_sent = self.insert_sentence("video", self.schema["video"].keys())
            video_data = self.extract_data(self.schema["video"], item, jane_key="title")

            self.db_cursor.execute(video_sent, video_data)
            self.db_connection.commit()
            # self.db_cursor.execute("SELECT id FROM video WHERE name=%s LIMIT 1;", \
            #                         (item['title'], item['rate']))
            # item["video_id"] = self.db_cursor.fetchone()[0]
        except TypeError as err:
            self.error_file_store.write(json.dumps(dict(item, query_step="video"), ensure_ascii=False) + "\n")
            self.log(f"Insert value error: {item}, because {err}",level=logging.ERROR)
        except Exception as err:
            self.error_file_store.write(json.dumps(dict(item, query_step="video"), ensure_ascii=False) + "\n")

        self.db_cursor.execute("SELECT id FROM video WHERE `name` = %s ORDER BY create_time DESC;", \
            (item['title'],))
        item["video_id"] = self.db_cursor.fetchone()[0]

        # store actor data into table, and query id
        actor_sent = self.insert_sentence("video_actor", self.schema["video_actor"].keys())
        actors_data = self.extract_list(item["actors"], True, item["video_id"])

        if len(actors_data) > 0:
            insert(actor_sent, actors_data, query_step="actor", single_query=False) # insert step
            # query id 
            
            query_sent = f"SELECT DISTINCT id FROM video_actor WHERE `name` in ({'%s, ' * (len(actors_data)-1)}%s) AND `video_id`=%s;"
            query_condition = [i[1] for i in actors_data] + [item["video_id"]]
            self.db_cursor.execute(query_sent, tuple(query_condition))
            actors_id = [i[0] for i in self.db_cursor.fetchall()]
        else:
            self.log(f"{item['id']} doesn't contain <actors>", level=logging.INFO)
            actors_id = []
        
        # store director data into table, and query id
        director_sent = self.insert_sentence("video_director", self.schema["video_director"].keys())
        directors_data = self.extract_list(item["director"], True, item["video_id"])
        insert(director_sent, directors_data, query_step="director", single_query=False)
        
        # query id
        if len(directors_data) > 0:
            query_sent  = f"SELECT DISTINCT id FROM video_director WHERE `name` in ({'%s, ' * (len(directors_data)-1)}%s) AND `video_id`=%s;"
            query_condition = [i[1] for i in directors_data] + [item["video_id"]]
            self.db_cursor.execute(query_sent, tuple(query_condition))
            directors_id = [i[0] for i in self.db_cursor.fetchall()]
        else:
            self.log(f"{item['id']} doesn't contain <directors>", level=logging.INFO)
            directors_id = []
        
        # store category data into table
        category_sent = self.insert_sentence("video_type", self.schema["video_type"].keys())
        category_data = self.extract_list(item["category"], appendix=item["video_id"])
        if len(category_data) > 0:
            insert(category_sent, category_data, query_step="category", single_query=False)
        else:
            self.log(f"{item['id']} doesn't contain <category>", level=logging.INFO)
        
        # store review data into table
        review_sent = self.insert_sentence("video_review", self.schema["video_review"].keys())
        reviews = json.loads(item["short_comment"])
        
        review_data = [(item["video_id"], index, time_, score, content)  \
                for index, (time_, score, content) in enumerate(zip(
                    reviews["time"], reviews["rate"], reviews["comment"]))]
        if len(review_data) > 0:
            insert(review_sent, review_data, query_step="review", single_query=False)
        else:
            self.log(f"{item['id']} doesn't contain <review>", level=logging.INFO)
        # store video extension region
        """
        [(1, '中国大陆', '2019', '2020', '135分钟', 0),
        (1, '美国', '2019', '2019-12-25', '135分钟', 0)]
        """
        extension_region_sent = self.insert_sentence("video_extension_region", \
                                self.schema["video_extension_region"].keys())
        
        regions = self.extract_list(item["play_location"])
        release_times = self.extract_list(item["play_year"])
        extension_region_data = []
        for region, time_ in zip(regions, release_times):
            extension_region_data.append((item["video_id"], region, \
                            item["release_year"], time_, item["play_duration"], 0))
        if len(extension_region_data) > 0:
            insert(extension_region_sent, extension_region_data, \
                query_step="video_extention_region", single_query=False)
        else:
            self.log(f"{item['id']} doesn't contain <extention region>", level=logging.INFO)

        # store role information into table
        character_role_sent = self.insert_sentence("video_character", \
                            self.schema["video_character"].keys())
        character_role_data = [(item['video_id'], index, name, role, url) \
                                for index, (name, role, url) in \
                        enumerate(zip(*json.loads(item["worker_detail"]).values()))]
        
        if len(character_role_data) >= 1:
            insert(character_role_sent, character_role_data, \
            query_step="video_character", single_query=False)
        else:
            self.log(f"Data id: {item['id']} has no character information!")
        

        return item

    
    def close_spider(self, spider):
        """Close Spider"""
        self.db_connection.close()
        self.redis_pool.close()
        self.error_file_store.close()
        self.file.close()


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


class ListPipeline(BaseSQLPipeline):
    """
    存储列表数据
    """
    db_type = "mysql"

    def __init__(self, basic_config, redis_config, schema, **kwargs):
        self.basic_config = basic_config
        self.redis_config = redis_config
        self.schema = schema 
        self._options = kwargs


    @classmethod
    def from_crawler(cls, crawler):
        schema = {
            "tag": "tag",
            "title": "title",
            "url": "url",
            "list_id": "list_id",
            "cover_link": "cover_url",
            "rate": "rate"
        }
        settings = crawler.settings["DATABASE_CONF"]
        basic_config = copy.deepcopy(settings[cls.db_type])
        redis_config = settings["redis"]
        

        return cls(
            basic_config=basic_config,
            redis_config=redis_config,
            schema=schema
        )


    def open_spider(self, spider):
        self.redis_pool = self.create_connection("redis", self.redis_config)
        self.db_connection = self.create_connection(self.db_type, self.basic_config, **self._options)

        self.db_cursor = self.db_connection.cursor()
        # store the exceptions data item
        self.error_file_store = open(path.join(cur_path, f"log/err_{spider.name}.txt"), "a")
        
    
    def process_item(self, item, spider):
        # 如果不是 ListItem 的数据，直接返回
        if not isinstance(item, ListItem):
            return item

        sentence = self.insert_sentence("list_series", self.schema.keys())
        data = tuple(item.values())
        self.db_cursor.execute(sentence, data)
        self.db_connection.commit()


        # ! 处理完列表页数据，不需要后续在进行处理，直接 DropItem
        raise DropItem(f"影视详情条目写入完成删除 {item['list_id']}: {item['name']}")


    def close_spider(self, spider):
        """Close Spider"""
        self.db_connection.close()
        self.redis_pool.close()
        self.error_file_store.close()



class DouBanDetailPipeline(BasePipeline):
    def process_item(self, item, spider):
        """处理豆瓣影视详情页数据

        """
        if not isinstance(item, DouBanDetailItem):
            return item
        
        with manipulater.get_session() as session:
            # 根据全局配置参数 update_table 确认是否需要更新
            if spider.config.getboolean("douban_seed", "update_table"):
                temp = session.query(DouBanSeriesSeed).filter(DouBanSeriesSeed.series_id==item["series_id"]).first()
                if temp:
                    temp.crawled = True
                    session.merge(temp)
                    session.commit()
                    self.log(f"Update Seed Status: {temp.series_id}")
            
            data = DouBanSeriesInfo(**item)
            session.merge(data)
            session.commit()
            self.logger.info(f"影视条目写入完成 {item['series_id']}: {item['name']}")




class DouBanAwardPipeline(BasePipeline):
    def process_item(self, item, spider):
        """处理豆瓣影视条目中获奖数据
        """
        if not isinstance(item, DouBanAwardItem):
            return item
        
        with manipulater.get_session() as session:
            data = DouBanSeriesAwards(**item)
            session.merge(data)
            session.commit()
            self.logger.info(f"获奖信息写入 awards 完成: {item['sid']}")



class DouBanWorkerPipeline(BasePipeline):
    def process_item(self, item, spider):
        """处理豆瓣影视演职人员数据
        """
        if not isinstance(item, DouBanWorkerItem):
            return item

        with manipulater.get_session() as session:
            data = DouBanSeriesWorker(**item)
            query = session.query(DouBanSeriesWorker).filter_by(sid=item["sid"]).first()

            if query:
                data.wid = query.wid
                
            session.merge(data)
            session.commit()
            self.logger.info(f"演职人员信息写入 worker 完成: {item['sid']}")



class DouBanPeoplePipeline(BasePipeline):
    def open_spider(self, spider):
        # import ipdb; ipdb.set_trace()
        port = configure.parser.getint("mongodb", "port")
        host = configure.parser.get("mongodb", "host")
        tz_aware = configure.parser.getboolean("mongodb", "tz_aware")
        minPoolSize = configure.parser.getint("mongodb", "minPoolSize")
        database = configure.parser.get("mongodb", "database")
        collection = configure.parser.get("mongodb", "person_collection")

        self.mongo_client = pymongo.MongoClient(port=port, host=host, \
            tz_aware=tz_aware, minPoolSize=minPoolSize)
        self.database = self.mongo_client[database]
        self.collection = self.database[collection]
        self.logger.info("连接到 MongoDB 服务器")


    def process_item(self, item, spider):
        """处理豆瓣影视演职人员 Profile数据
        
        """
        if not isinstance(item, DouBanPeopleItem):
            return item

        # 如果 DouBanPeopleItem 中没有 name 数据后，那么说明需要不需要传入到 MySQL 数据库
        # 该条数据是表示的是关于演职人员的 图片信息，数据是 array——解析的 item 来源是 
        # parse_person_imgs
        # * 需要将数据写入到 MongoDB 中
        query_item = self.collection.find_one({"id": item['id']})
        if query_item:
            self.collection.update_one({"_id": query_item.get('_id')}, {"$set": dict(item)})
            self.logger.info(f"更新演职人员数据(MongoDb): {item['id']}")
        else:
            self.collection.insert_one(dict(item))
            self.logger.info(f"插入演职人员数据(MongoDb): {item['id']}")
        
        with manipulater.get_session() as session:
            del item['imgs'], item['imgs_content']
            data = DouBanSeriesPerson(**item)
            session.merge(data)
            session.commit()
            self.logger.info(f"演职人员 Profile 信息写入 people 完成: {item['id']}")
            

    def close_spider(self, spider):
        # 关闭链接
        self.mongo_client.close()
        
        
class DouBanPicturePipeline(BasePipeline):
    def process_item(self, item, spider):
        """处理豆瓣影视海报、剧照以及壁纸
        
        """
        if not isinstance(item, DouBanPhotosItem):
            return item

        with manipulater.get_session() as session:
            data = DouBanSeriesPic(**item)
            session.merge(data)
            session.commit()
            self.logger.info(f"影视海报等图片信息写入 picture 完成: {item['sid']}")
        


class DouBanEpisodePipeline(BasePipeline):
    def process_item(self, item, spider):
        """处理豆瓣影视剧集信息
        """
        if not isinstance(item, DouBanEpisodeItem):
            return item

        with manipulater.get_session() as session:
            data = DouBanEpisodeInfo(**item) 
            query = session.query(DouBanEpisodeInfo).filter_by(sid=item["sid"], episode=item["episode"]).first()

            if query:
                data.id = query.id
            
            session.merge(data)
            session.commit()
            self.logger.info(f"影视剧集信息写入 episode_info 完成：{item['sid']}")

        


class DouBanCommentPipelineM(BasePipeline):
    def open_spider(self, spider):
        # import ipdb; ipdb.set_trace()
        port = configure.parser.getint("mongodb", "port")
        host = configure.parser.get("mongodb", "host")
        tz_aware = configure.parser.getboolean("mongodb", "tz_aware")
        minPoolSize = configure.parser.getint("mongodb", "minPoolSize")
        database = configure.parser.get("mongodb", "database")
        collection = configure.parser.get("mongodb", "comments_collection")

        self.mongo_client = pymongo.MongoClient(port=port, host=host, \
            tz_aware=tz_aware, minPoolSize=minPoolSize)
        self.database = self.mongo_client[database]
        self.collection = self.database[collection]
        self.logger.info("连接到 MongoDB 服务器")

    
    def process_item(self, item, spider):
        """豆瓣评论数据

        豆瓣评论数据是写入 MongoDB 中，保存数据的 connection 是 comments
        """
        if not isinstance(item, DouBanCommentsItemM):
            return item

        query_item = self.collection.find_one({"comment_id": item['comment_id']})
        if query_item:
            self.collection.update_one({"_id": query_item.get('_id')}, {"$set": dict(item)})
            self.logger.info(f"更新评论数据: {item['comment_id']}")
        else:
            self.collection.insert_one(dict(item))
            self.logger.info(f"插入评论数据: {item['comment_id']}")
        

    
    def close_spider(self, spider):
        # 关闭链接
        self.mongo_client.close()