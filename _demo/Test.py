from playhouse.pool import PooledMySQLDatabase

import json
from bson import json_util

from playhouse.shortcuts import model_to_dict, dict_to_model

from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField,
    BlobField
)


database = PooledMySQLDatabase(
    'test',
    max_connections=8,
    stale_timeout=10,
    host='localhost',
    port=3306,
    user='root',
    password='root'
)

class Test(Model):
    id = IntegerField()
    name = CharField(max_length=100)
    date = DateTimeField()

    class Meta:
        database = database
        table_name = "test"

# 如果数据库中不存在表，则创建表
database.connect()
database.create_tables([Test], safe=True)

def select_all():
    """查询所有数据"""
    ret = Test.select()
    for obj in ret:
        model_obj = model_to_dict(obj)
        print(model_obj)
        # json_obj = json.dumps(model_obj)
        # print(json_obj)