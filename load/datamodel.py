#coding:utf8
"""
MySQL 数据表的数据模型:
1. TempItem 是 `series_temp` 表的数据库模型
"""
import sqlalchemy
import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func

# declarative Base
Base = declarative_base()



class DouBanSeriesSeedItem(Base):
    """外源信息临时表

    外源信息临时表，用于存储需要影视信息种子源。表名是 `series_temp`，schema 信息可以通过
    `douban_series.sql` 文件中确认
    """
    __tablename__ = "series_seed"
    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(length=20, convert_unicode=True), nullable=False, unique=True)
    title = sqlalchemy.Column(sqlalchemy.VARCHAR(150, convert_unicode=True, collation="utf8mb4"), nullable=False)
    main_tag = sqlalchemy.Column(sqlalchemy.VARCHAR(10, convert_unicode=True, collation="utf8mb4"), nullable=True)
    status = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    create_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=func.now())
    update_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


    def __repr__(self):
        format = "<Data Model Object: %s at %s>"
        return format % (self.__class__.__tablename__, hex(id(self)))

    def __str__(self):
        string = f"Item data:\n\t ID: {self.id} Series_ID: {self.series_id}" + \
                f" Title: {self.title} Status: {self.status}"
        return string