#coding:utf8
"""
解析数据库配置信息
"""
import configparser
import os

# config file
file = os.path.join(os.path.dirname(__file__), "./database.ini")

class Config:
    def __init__(self, filename):
        # create parser object
        self.parser = configparser.ConfigParser()
        self.read(filename)

    def read(self, filename):
        """解析出配置信息

        解析指定文件中的配置信息
        """
        # check file existed
        if not os.path.exists(filename):
            raise FileNotFoundError(f"{filename} doesn't exist")

        self.parser.read(filename)


    @property
    def mysql(self):
        """MySQL 全局配置信息
        """
        self.__check_section("mysql")

        config = {key: self.parser.get("mysql", key) for key in \
            self.parser.options("mysql")}
        
        return config


    @mysql.setter
    def mysql(self, key, value):
        """MySQL 配置信息设置

        不允许修改原始配置信息
        """
        NotImplemented


    def __check_section(self, section):
        """检测 section

        检查 section 是否存在
        """
        if not self.parser.has_section("mysql"):
            raise LookupError("There is not mysql Secton in configuration")
        else:
            pass


configure = Config(file)

__all__ = ["configure"]