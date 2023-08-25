import json

import jsonpickle
from flask import session
from peewee import (
    Model,
    CharField,
    DateTimeField,
    AutoField,
    Index
)

from common.db.dbconfig import db


class Prompt(Model):
    id = AutoField()
    act = CharField(unique=False, max_length=32)
    prompt = CharField(null=False, max_length=1024)
    owner_id = CharField(index=True,null=True, max_length=32, default='system')
    disabled = CharField(max_length=1, default='0')
    created_time = DateTimeField()
    updated_time = DateTimeField()

    @staticmethod
    def get_available_prompts(owner_id='system'):
        #query prompts from db where owner_id = 'system' or owner_id = self.user_id
        prompts = (Prompt
                   .select(Prompt.id, Prompt.act, Prompt.prompt)
                   .where((Prompt.owner_id == owner_id) | (Prompt.owner_id == 'system'),
                          Prompt.disabled == '0')
                   .dicts()
                   )
        return list(prompts)


    def __str__(self):
        return jsonpickle.encode(self, unpicklable=False)
    def to_json(self):
        return json.loads(jsonpickle.encode(self, unpicklable=False))
    def to_dict(self):
        return json.loads(jsonpickle.encode(self, unpicklable=False))
    class Meta:
        database = db
        table_name = "prompt"



# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([Prompt], safe=True)
db.close()
