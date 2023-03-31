
from config import config
from common import const
from playhouse.pool import PooledMySQLDatabase

host = config.get(const.MYSQL).get('host')
userName = config.get(const.MYSQL).get('userName')
password = config.get(const.MYSQL).get('password')
db = config.get(const.MYSQL).get('db')

from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField,
    BlobField
)

db = PooledMySQLDatabase(
    db,
    max_connections=8,  # 连接池允许的最大连接数量
    stale_timeout=10,  # 一个连接未使用多长时间后被视为“过时”并丢弃
    host=host,
    port=3306,
    user=userName,
    password=password,
    charset='utf8mb4'
)


class DocumentRecord(Model):
    id = AutoField()
    user_id = IntegerField()
    title = CharField(unique=True, max_length=255)
    path = CharField(max_length=255)
    deleted = BooleanField()
    read_count = IntegerField()
    created_time = DateTimeField()
    updated_time = DateTimeField()
    trained = BooleanField()

    class Meta:
        database = db
        table_name = "document_reocrd"

# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([DocumentRecord], safe=True)
    