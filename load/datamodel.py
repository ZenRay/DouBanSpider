#coding:utf8
"""
MySQL 数据表的数据模型:
1. TempItem 是 `series_temp` 表的数据库模型
"""
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

# declarative Base
Base = declarative_base()



class TempItem(Base):
    """外源信息临时表

    外源信息临时表，用于存储需要影视信息种子源。表名是 `series_temp`，schema 信息可以通过
    `douban_series.sql` 文件中确认
    """
    __tablename__ = "series_temp"
    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    series_id = sqlalchemy.Column(sqlalchemy.VARCHAR(length=20, convert_unicode=True), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.VARCHAR(150, convert_unicode=True, collation="utf8mb4"), nullable=False)
    main_tag = sqlalchemy.Column(sqlalchemy.VARCHAR(10, convert_unicode=True, collation="utf8mb4"), nullable=True)
    status = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    create_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    update_time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)


    def __repr__(self):
        format = "<Data Model Object: %s at %s>"
        return format % (self.__class__.__tablename__, hex(id(self)))