#coding:utf8
from __future__ import absolute_import

import contextlib
import pandas as pd
import sqlalchemy
from sqlalchemy import orm

from .datamodel import Base

from ..conf import configure

# database URI information
URI = "mysql+pymysql://{user}{password}@{host}:{port}/{database}?charset={charset}"

password = "" if not configure.mysql.get("password") else f':{configure.mysql.get("password")}'
URI = URI.format(
    user=configure.mysql.get("user"), password=password,
    host=configure.mysql.get('host'), port=configure.mysql.get("port"),
    charset= configure.mysql.get("charset"), database=configure.mysql.get("database")
)


__all__ = ["DataBaseManipulater"]

class DataBaseManipulater(object):
    """使用 SQLAlchemy 操作数据
    操作数据:
    1. 写入数据
    2. 查询数据
    """
    def __new__(cls, *args, **kwargs):
        instance = super(DataBaseManipulater, cls).__new__(cls)
        instance.Session = sqlalchemy.orm.sessionmaker()
        
        return instance


    def __init__(self, *args, **kwargs):
        """Initial Object

        如果需要创建一个新对象的话，可以根据需要确认是否需要输出日志信息。需要使用关键字参数 
        `echo` 为 True
        """
        # create table, pass `checkfirst=True`, so that enforce check existence 
        # before create table
        self._engine = sqlalchemy.create_engine(URI, echo=kwargs.get("echo", False))
        Base.metadata.create_all(self._engine, checkfirst=True)


    def __enter__(self):
        self.Session.configure(bind=self._engine)
        self.__session = self.Session()
        return self.__session


    def __exit__(self, type, value, traceback):
        self.Session.kw["bind"] = None
        self.__session.close()
        return True

    
    @contextlib.contextmanager
    def get_session(self, *args, **kwargs):
        """session 上下文管理方法

        session 对象，用于对数据操作。在开始前会绑定一个 self._engine，接受自定义的 engine。第一
        个默认的位置参数优先作为 engine，或者接受一个 bind 的关键字参数
        """
        # check whether engine binded, if there is not engine,
        if len(args) >= 1:
            self.Session.configure(bind=args[0])
        elif "bind" in kwargs:
            self.Session.configure(bind=kwargs['bind'])
        else:
            self.Session.configure(bind=self._engine)

        # 创建 session 对象
        session = self.Session()

        try:
            yield session
        except sqlalchemy.exc.StatementError as error:
            session.rollback()
            raise sqlalchemy.exc.StatementError(error)
        finally:
            # recover engine is None
            self.Session.kw["bind"] = None
            session.close()

