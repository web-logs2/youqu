import json

from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField,
    DoubleField
)

from common.db.dbconfig import db
from common.functions import get_city_name_in_chinese


class Transaction(Model):
    id = AutoField()
    user_id = CharField(unique=False, max_length=64)
    transaction_id = CharField(unique=False, max_length=64)
    amount = DoubleField(unique=False, default=0)
    status = IntegerField(unique=False, default=0)  # 0: pending, 1: success, 2: failed 3: refunded 4: cancelled
    channel = CharField(unique=False, max_length=2)  # 0: lantu-wechat
    ip = CharField(unique=False, max_length=128)
    ip_location = CharField(unique=False, max_length=1024)
    created_time = DateTimeField()
    updated_time = DateTimeField()

    def update_ip_location(self):
        self.ip_location = get_city_name_in_chinese(self.ip)

    class Meta:
        database = db
        table_name = "query_record"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([Transaction], safe=True)
db.close()
