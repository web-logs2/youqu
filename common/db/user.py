import json

from peewee import (
    Model,
    CharField,
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
    available_models = CharField(null=True, max_length=1024, default='["gpt-3.5-turbo"]')
    deleted = CharField(max_length=1, default='0')
    last_login = DateTimeField()
    created_time = DateTimeField()
    updated_time = DateTimeField()

    def set_available_models(self, models_list):
        self.available_models = json.dumps(models_list)

    def get_available_models(self):
        if self.available_models is not None:
            return json.loads(self.available_models)
        return None

    class Meta:
        database = db
        table_name = "user"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([User], safe=True)
db.close()
