
from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    DateTimeField,
    AutoField
)

from common.db.dbconfig import db

class DocumentRecord(Model):
    id = AutoField()
    user_id = IntegerField()
    title = CharField(unique=True, max_length=255)
    path = CharField(max_length=255)
    deleted = BooleanField()
    read_count = IntegerField()
    created_time = DateTimeField()
    updated_time = DateTimeField()
    trained = BooleanField()
    trained_file_path = CharField(unique=True, max_length=512)

    class Meta:
        database = db
        table_name = "document_reocrd"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([DocumentRecord], safe=True)
db.close()
