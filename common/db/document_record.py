import datetime

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
    user_id = CharField(unique=False, max_length=64)
    title = CharField(unique=True, max_length=255)
    path = CharField(max_length=255)
    deleted = BooleanField()
    read_count = IntegerField()
    created_time = DateTimeField()
    updated_time = DateTimeField()
    trained = BooleanField()
    training_status = IntegerField(default=0)   # 0:未开始 1:拒绝训练 2:可以训练 3:正在训练 4:训练完成
    trained_file_path = CharField(unique=True, max_length=512)
    # 1.书籍       book
    # 2.博客园     cnblogs
    type = CharField(default='', max_length=20)

    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "trained": self.trained,
            "type": self.type
        }

    #query all available documents
    @staticmethod
    def query_all_available_documents(user_id):
        #return all documents to string
        #,DocumentRecord.user_id==user_id
        documents: list[DocumentRecord] = DocumentRecord.select().where(DocumentRecord.deleted == 0,DocumentRecord.trained==1)
        document_list = []
        for document in documents:
            document_list.append(document.dict())
        return document_list



    def save(self, *args, **kwargs):
        self.updated_time = datetime.datetime.now()
        return super().save(*args, **kwargs)

    class Meta:
        database = db
        table_name = "document_record"

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
