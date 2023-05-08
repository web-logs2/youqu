
from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField
)

from common.db.dbconfig import db

class Conversation(Model):
    id = AutoField()
    conversation_id = CharField(unique=True, max_length=64)
    user_id = CharField(unique=False, max_length=64)
    promote = CharField(unique=False, max_length=200)
    total_query = IntegerField()
    created_time = DateTimeField()
    updated_time = DateTimeField()

    class Meta:
        database = db
        table_name = "conversation"
# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([Conversation], safe=True)
db.close()
