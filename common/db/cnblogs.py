from playhouse.pool import PooledMySQLDatabase

from common import const
from config import config

host = config.get(const.MYSQL).get('host')
userName = config.get(const.MYSQL).get('userName')
password = config.get(const.MYSQL).get('password')
db = config.get(const.MYSQL).get('db')

from peewee import (
    Model,
    IntegerField,
    CharField,
    DateTimeField,
    AutoField,
    TextField,
    BooleanField
)

db = PooledMySQLDatabase(
    db,
    max_connections=20,  # 连接池允许的最大连接数量
    stale_timeout=10,  # 一个连接未使用多长时间后被视为“过时”并丢弃
    host=host,
    port=3306,
    user=userName,
    password=password,
    charset='utf8mb4'
)

class CnblogsAuthor(Model):
    id = AutoField()
    name = CharField(max_length=255)
    home_path = CharField(max_length=255)
    read_count = IntegerField(default=0)
    trained = BooleanField(default=False)
    trained_file_path = CharField(default='', max_length=512)
    created_time = DateTimeField()
    updated_time = DateTimeField()

    class Meta:
        database = db
        table_name = "cbnlogs_author"

# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([CnblogsAuthor], safe=True)
