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
from common.functions import get_city_name_in_chinese


class QueryRecord(Model):
    id = AutoField()
    user_id = CharField(unique=False, max_length=64)
    conversation_id = CharField(unique=False, max_length=64)
    query = CharField(unique=False, max_length=30000)
    reply = CharField(unique=False, max_length=30000)
    ip = CharField(unique=False, max_length=128)
    ip_location = CharField(unique=False, max_length=1024)
    query_trail = CharField(unique=False, max_length=100000)
    model_name = CharField(unique=False, max_length=64)
    prompt_count = IntegerField(unique=False, default=0)
    complication_count = IntegerField(unique=False, default=0)
    created_time = DateTimeField()
    updated_time = DateTimeField()

    def set_query_trail(self, query_trail):
        self.query_trail = json.dumps(query_trail, ensure_ascii=False)

    def get_query_trail(self):
        if self.query_trail is not None:
            return json.loads(self.query_trail, encoding='utf-8')
        return None

    def update_ip_location(self):
        self.ip_location = get_city_name_in_chinese(self.ip)

    class Meta:
        database = db
        table_name = "query_record"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([QueryRecord], safe=True)
db.close()
