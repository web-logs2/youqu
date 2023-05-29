import json

from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField
)

from common.db.dbconfig import db

class QueryRecord(Model):
    id = AutoField()
    user_id = CharField(unique=False, max_length=64)
    conversation_id = CharField(unique=False, max_length=64)
    query = CharField(unique=False, max_length=30000)
    reply = CharField(unique=False, max_length=30000)
    ip = CharField(unique=False, max_length=128)
    ip_location=CharField(unique=False, max_length=1024)
    query_trail=CharField(unique=False, max_length=100000)
    model_name= CharField(unique=False, max_length=64)
    created_time = DateTimeField()
    updated_time = DateTimeField()

    def set_query_trail(self, query_trail):
        self.query_trail = json.dumps(query_trail)

    def get_query_trail(self):
        if self.query_trail is not None:
            return json.loads(self.query_trail)
        return None


    class Meta:
        database = db
        table_name = "query_reocrd"

# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([QueryRecord], safe=True)
db.close()
