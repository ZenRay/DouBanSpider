#coding:utf8

import pandas as pd
import sqlalchemy
from sqlalchemy import orm

from .datamodel import TempItem
from .conf import configure

# database URI information
URI = "mysql+pymysql://{user}{password}@{host}:{port}/{database}?charset={charset}"

password = "" if not configure.mysql.get("password") else f':{configure.mysql.get("password")}'
URI = URI.format(
    user=configure.mysql.get("user"), password=password,
    host=configure.mysql.get('host'), port=configure.mysql.get("port"),
    charset= configure.mysql.get("charset"), database=configure.mysql.get("database")
)




def load_movies(file):
    df = pd.read_csv(file)
    df["TITLE"] = df.NAME.str.replace(" - 电影| - 电视剧", "")

    # select data
    data = df.loc[:, ["MOVIE_ID", "NAME", "TITLE"]]
    return data


class Connection:
    """Connect Database With SQLalchemy

    The object is supported by a context manger, which can use `with` expression.

    Property:
        _engine: Connect a database engine object

    Method:
        query: Use it's own context manager to query a latest `Opinion` data, 
            if `update` is True, update the tenden status
    """
    def __init__(self):
        self._engine = sqlalchemy.create_engine(URI)
        self.__Session = orm.sessionmaker()

    
    def __enter__(self):
        self.__Session.configure(bind=self._engine)
        self.session =  self.__Session()
        return self.session


    def __exit__(self, type, value, traceback):
        self.session.close()
        return True
        