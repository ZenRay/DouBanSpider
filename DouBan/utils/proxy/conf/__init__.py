#coding:utf8
import configparser
import os

# config file
file = os.path.join(os.path.dirname(__file__), "./proxy.ini")

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


configure = Config(file)

__all__ = ["configure"]