
from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField
)

from common.db.dbconfig import db

class User(Model):
    id = AutoField()
    user_id = CharField(unique=True, max_length=256)
    user_name = CharField(unique=False, max_length=32)
    email = CharField(unique=True, max_length=256)
    phone = CharField(unique=True, max_length=64)
    password = CharField(unique=False, max_length=512)
    last_login= DateTimeField()
    created_time = DateTimeField()
    updated_time = DateTimeField()

    class Meta:
        database = db
        table_name = "user"

# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([User], safe=True)
db.close()
