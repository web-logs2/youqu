
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
    user_id = CharField(unique=True, max_length=64)
    title = CharField(unique=True, max_length=255)
    path = CharField(max_length=255)
    deleted = BooleanField()
    read_count = IntegerField()
    created_time = DateTimeField()
    updated_time = DateTimeField()
    trained = BooleanField()
    trained_file_path = CharField(unique=True, max_length=512)
    # 1.书籍       book
    # 2.博客园     cnblogs
    type = CharField(default='', max_length=20)

    class Meta:
        database = db
        table_name = "document_reocrd"

    @staticmethod
    def type_mapping(type) -> any:
        if "book" == type:
            return "书籍"
        elif "cnblogs" == type:
            return "博客园"
        elif "wx" == type:
            return "微信公众号"
        else:
            return "书籍"

# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([DocumentRecord], safe=True)
db.close()
