#-*-coding:utf-8 -*-
"""
The module is a tool to create base object
"""
import logging
import scrapy
import sqlite3
import pymysql
import redis
import inspect
import re


from .exceptions import (
    InappropriateArgument,
    InvalidateConfigure,
    LostArgument,
    ConnectionError
)


__all__ = ["BaseSQLPipeline" , "BaseSpider"]

class BaseSQLPipeline(object):
    """Generate table config
    Store table config
    """
    @property
    def logger(self):
        """Set property logger"""
        logger = logging.getLogger(self.__class__.__name__)
        return logging.LoggerAdapter(logger, {"SQLPipeline": self})


    def log(self, message, level=logging.DEBUG, **kwargs):
        """Run logger to display log information"""
        self.logger.log(level, message, **kwargs)


    def create_connection(self, database_type, basic_config, **kwargs):
        """Connect database
        Connect database, and it supports mysql, redis or sqlite. The arguments 
        are different according by the database type.
        Args:
            database_type: database managent system type, specify what the 
                database is, like mysql, sqlite, redis
            basic_config: dict value, contains most of database configuration. Value 
                like that:
                    'sqlite': {
                        'path': './data/data',
                        'cache_path': './data/cached/'
                        }, 
                    'database': 'public_opinion_forhzjy'
                    }
            kwargs: connect database argument
        
        Returns:
            connect: database connection object
        Examples:
            There are three main types basic_config:
            >>> # This is sqlite config
            >>> basic_config = {
            >>>    'path': './data/data', 
            >>>    'cache_path': './data/cached/', 
            >>>    'database': 'public_opinion_forhzjy'
            >>> }
            >>> connection = create_connection(**basic_config, **kwargs)
            >>> cursor = connection.cursor()
        """
        if database_type == "mysql":
            # parse mysql configuration
            database_config  = {}
            for key, value in basic_config.items():
                if key in inspect.getfullargspec(pymysql.connections.Connection.__init__)[0]:
                    database_config[key] = value

            connect = pymysql.connect(**database_config, **kwargs)
        elif database_type == "sqlite":
            if not basic_config["database"].endswith(r".db"):
                basic_config["database"] += r".db"
            path = basic_config["path"] + basic_config["database"]
            connect = sqlite3.connect(path, **kwargs)
        elif database_type == "redis":
            connect = redis.StrictRedis(connection_pool=redis.ConnectionPool(
                **basic_config, **kwargs))
            # check the connection status
            if not connect.ping():
                raise ConnectionError("Can't connect the redis server. Checkout" + 
                                    " network and config parameters.")
        else:
            raise InappropriateArgument("Database type is inappropriate, and \
                value is {0}".format(database_type))

        return connect

    def __check_attribute(self, name):
        """Check attribute
        Check attribute name whether it exists. If it doesn't exist, return True,
        else return False.
        """
        try:
            object.__getattribute__(self, name)
            return False
        except AttributeError:
            return True


    def set_table_attribute(self, tb_config, config_dict:dict):
        """Generate table config
        Setup the database with basic config and database config.
        
        Args:
            tb_config: default dict. Store all table config
            config_dict: defaul dict. Store attribute name map with tb_config key name
        Example:
            >>> test = BaseSQLPipeline()
            >>> tb_config = {
                    "table": "tbl_top_event",
                    "fields": (
                    "event_name", "topic_quantity", "collect_time", "read_num", "discuss_num", "status"
                    )
                }
            >>> config_dict = {
                    "event_table": "table",
                    "event_fields": "fields"
                }
            >>> test.table_config(tb_config, config_dict)
            >>> test.event_table
                'tbl_top_event'
            >>> test.event_fields
                ('event_name',
                'topic_quantity',
                'collect_time',
                'read_num',
                'discuss_num',
                'status')
        """
        for attribute, key in config_dict.items():
            if self.__check_attribute(attribute):
                self.__dict__[attribute] = tb_config[key]
            else:
                raise ValueError("Attribute name duplicated, check config_dict", 
                    config_dict)

    
    def insert_sentence(self, table, fields, symbol=r"%s"):
        """Create SQL insert sentence
        Create a insert sentence, like that:
            INSERT INTO <table> (`col1`, `col2`) VALUES (%s, %s)
        """
        sentence = """
            INSERT INTO {tb} {fieldnames} VALUES {values_symbol};
        """

        fieldnames = "({column})".format(
            column=",".join("`{}`".format(field) for field in fields)
        )

        values_symbol = "(" + ",".join((symbol for i in range(len(fields)))) + ")"

        sentence = sentence.format(
            tb=table, fieldnames=fieldnames, values_symbol=values_symbol
        )

        return sentence



class BaseSpider(scrapy.Spider):
    """Base class for spider extension
    """
    def __init__(self, mark_name="", **kwargs):
        super().__init__(**kwargs)
        self.mark_name = mark_name


    @property
    def logger(self):
        """Set property logger"""
        logger = logging.getLogger(self.__class__.__name__)
        return logging.LoggerAdapter(logger, {"Spider": self})


    def log(self, message, level=logging.DEBUG, **kwargs):
        """Run logger to display log information"""
        spider_name = kwargs.pop("spider", self.mark_name)

        message = "Spider {key}: {msg}".format(key=spider_name,  msg=message)
        super().log(message=message, level=level, **kwargs)


