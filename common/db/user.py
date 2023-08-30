import json

import jsonpickle
from flask import session
from peewee import (
    Model,
    CharField,
    DateTimeField,
    AutoField,
    DecimalField, FieldAccessor
)
from playhouse.migrate import MySQLMigrator, migrate

from common.db.db_utils import add_field_if_not_exist
from common.db.dbconfig import db


class User(Model):
    id = AutoField()
    user_id = CharField(unique=True, max_length=256)
    user_name = CharField(unique=False, max_length=32)
    email = CharField(unique=True, max_length=256)
    phone = CharField(unique=True, max_length=64)
    password = CharField(unique=False, max_length=512)
    available_models = CharField(null=True, max_length=1024, default='["gpt-3.5-turbo"]')
    available_balance = DecimalField(null=False, default=0, max_digits=18, decimal_places=10)
    avatar = CharField(max_length=1024, default='')
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

    def set_available_balance(self, balance):
        self.available_balance = json.dumps(balance)

    def get_available_balance(self):
        if self.available_balance is not None:
            return json.loads(self.available_balance)
        return 0
    def get_available_balance_round2(self):
        if self.available_balance is not None:
            return round(self.available_balance, 2)
        return 0

    def save_in_session(self):
        if self is not None:
            session["user"] = jsonpickle.encode(self)

    def delete_from_session(self):
        if "user" in session:
            del session["user"]

    def __str__(self):
        return json.dumps(self.dict())

    def __repr__(self):
        return json.dumps(self.dict())

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __ne__(self, other):
        return self.id != other.id

    def __lt__(self, other):
        return self.id < other.id

    def __le__(self, other):
        return self.id <= other.id

    def __gt__(self, other):
        return self.id > other.id

    def __ge__(self, other):
        return self.id >= other.id

    def __cmp__(self, other):
        return self.id - other.id

    @staticmethod
    def from_dict(user_json):
        user = User()
        user.id = user_json["id"]
        user.user_id = user_json["user_id"]
        user.user_name = user_json["user_name"]
        user.email = user_json["email"]
        user.phone = user_json["phone"]
        user.available_models = user_json["available_models"]
        user.available_balance = user_json["available_balance"]
        user.avatar = user_json["avatar"]
        user.deleted = user_json["deleted"]
        user.last_login = user_json["last_login"]
        user.created_time = user_json["created_time"]
        user.updated_time = user_json["updated_time"]
        return user

    def dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "email": self.email,
            "phone": self.phone,
            "available_models": self.get_available_models(),
            "available_balance": self.get_available_balance_json(),
            "avatar": self.avatar,
            "deleted": self.deleted,
            "last_login": self.last_login,
            "created_time": self.created_time,
            "updated_time": self.updated_time
        }

    @staticmethod
    # return user object from session
    def get_from_session():
        if "user" not in session:
            return None  # user not logged in
        return jsonpickle.decode(session["user"])

    class Meta:
        database = db
        table_name = "user"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([User], safe=True)
add_field_if_not_exist("user", "avatar", CharField(max_length=1024, default=''))
add_field_if_not_exist("user", "available_balance", DecimalField(null=False, default=0, max_digits=18, decimal_places=10))
db.close()
