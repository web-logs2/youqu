import datetime
import json
from decimal import Decimal

from peewee import (
    Model,
    IntegerField,
    CharField,
    DateTimeField,
    AutoField, DecimalField
)

from common.const import MODEL_GPT_35_TURBO, MODEL_GPT_35_TURBO_COMPLETION_PRICE, MODEL_GPT_35_TURBO_PROMPT_PRICE, \
    MODEL_GPT_35_turbo_16K, MODEL_GPT_4_PROMPT_PRICE, MODEL_GPT_4_COMPLETION_PRICE, \
    MODEL_GPT_35_TURBO_16K_COMPLETION_PRICE, MODEL_GPT_35_TURBO_16K_PROMPT_PRICE
from common.db.db_utils import add_field_if_not_exist
from common.db.dbconfig import db
from common.functions import get_city_name_in_chinese


class QueryRecord(Model):
    id = AutoField()
    message_id = CharField(index=True, unique=False, default="", max_length=64)  # 用户自己生成的 不可靠
    user_id = CharField(index=True, unique=False, max_length=64)
    conversation_id = CharField(index=True, unique=False, max_length=64)
    query = CharField(unique=False, max_length=30000)
    reply = CharField(unique=False, max_length=30000)
    ip = CharField(unique=False, max_length=128)
    ip_location = CharField(unique=False, max_length=1024)
    query_trail = CharField(unique=False, max_length=100000)
    model_name = CharField(unique=False, max_length=64)
    prompt_id = IntegerField(index=True,unique=False, default=0)
    like_or_dislike = CharField(unique=False, max_length=1, default='0')  # 0: no like or dislike, 1: like, 2: dislike
    cost = DecimalField(null=False, default=0, max_digits=18, decimal_places=10)
    prompt_count = IntegerField(unique=False, default=0)
    functions = CharField(unique=False, max_length=1024)
    complication_count = IntegerField(unique=False, default=0)
    created_time = DateTimeField()
    updated_time = DateTimeField()

    def set_query_trail(self, query_trail):
        self.query_trail = json.dumps(query_trail, ensure_ascii=False)

    def get_query_trail(self):
        if self.query_trail is not None:
            return json.loads(self.query_trail, encoding='utf-8')
        return None

    def set_functions(self, functions):
        self.functions = json.dumps(functions, ensure_ascii=False)

    def get_functions(self):
        if self.functions is not None:
            return json.loads(self.functions, encoding='utf-8')
        return None

    def update_ip_location(self):
        self.ip_location = get_city_name_in_chinese(self.ip)

    def get_query_record_dict(self):
        return {
            "reply": self.reply,
            "cost": str(self.cost),
            "prompt_count": str(self.prompt_count),
            "complication_count": str(self.complication_count),
        }

    def save(self, *args, **kwargs):
        self.updated_time = datetime.datetime.now()
        return super().save(*args, **kwargs)

    def set_cost(self):
        # cost = new Decimal 0
        cost = Decimal(0)

        if self.model_name == MODEL_GPT_35_TURBO:
            self.cost = MODEL_GPT_35_TURBO_COMPLETION_PRICE * self.complication_count + MODEL_GPT_35_TURBO_PROMPT_PRICE * self.prompt_count
        elif self.model_name == MODEL_GPT_35_turbo_16K:
            self.cost = MODEL_GPT_35_TURBO_16K_COMPLETION_PRICE * self.complication_count + MODEL_GPT_35_TURBO_16K_PROMPT_PRICE * self.prompt_count
        else:
            self.cost = MODEL_GPT_4_COMPLETION_PRICE * self.complication_count + MODEL_GPT_4_PROMPT_PRICE * self.prompt_count

    class Meta:
        database = db
        table_name = "query_record"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([QueryRecord], safe=True)
add_field_if_not_exist("query_record", "message_id", CharField(index=True, unique=False, default="", max_length=64))
add_field_if_not_exist("query_record", "prompt_id", IntegerField(index=True,unique=False, default=0))
add_field_if_not_exist("query_record", "like_or_dislike", CharField(unique=False, max_length=1, default='0'))
db.close()
