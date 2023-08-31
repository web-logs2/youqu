import datetime
import json

from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField,
    DecimalField
)

from common.db.dbconfig import db
from common.functions import get_city_name_in_chinese


class Transaction(Model):
    id = AutoField()
    user_id = CharField(unique=False, max_length=64)
    transaction_id = CharField(index=True,unique=True, max_length=64)
    amount = DecimalField(null=False, default=0, max_digits=18, decimal_places=2)
    status = IntegerField(unique=False, default=0)  # 0: pending, 1: success, 2: failed 3: refunded 4: cancelled
    channel = CharField(unique=False, max_length=2)  # 0: lantu-wechat
    ip = CharField(unique=False, max_length=128)
    ip_location = CharField(unique=False, max_length=1024)
    created_time = DateTimeField()
    updated_time = DateTimeField()

    def update_ip_location(self):
        try:
            self.ip_location = get_city_name_in_chinese(self.ip)
        except:
            self.ip_location = ""

    def save(self, *args, **kwargs):
        self.updated_time = datetime.datetime.now()
        return super(Transaction, self).save(*args, **kwargs)

    class Meta:
        database = db
        table_name = "transaction"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([Transaction], safe=True)
db.close()
