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


class Function(Model):
    id = AutoField()
    function_name = CharField(unique=False, max_length=32)
    available_models = CharField(null=True, max_length=1024, default='["gpt-3.5-turbo-16k"]')
    function_detail = CharField(null=False, max_length=10240)
    owner_id = CharField(index=True, null=True, max_length=32, default='system')
    type = CharField(null=False, max_length=32)
    use_case = CharField(null=True, max_length=512)
    disabled = CharField(max_length=1, default='0')
    created_time = DateTimeField()
    updated_time = DateTimeField()

    @staticmethod
    def get_available_functions(owner_id='system'):
        # query prompts from db where owner_id = 'system' or owner_id = self.user_id
        functions = (Function
                     .select(Function.id, Function.function_name, Function.use_case)
                     .where((Function.owner_id == owner_id) | (Function.owner_id == 'system'),
                            Function.disabled == '0')
                     .dicts()
                     )
        return list(functions)

    @staticmethod
    def get_function_by_owner_and_function_id(owner_id, function_ids=None):

        if function_ids:
            functions = (Function
                         .select(Function.function_detail)
                         .where((Function.owner_id == owner_id) | (Function.owner_id == 'system'),
                                Function.id.in_(function_ids),
                                Function.disabled == '0')
                         )
        else:
            functions = (Function
                         .select(Function.function_detail)
                         .where((Function.owner_id == owner_id) | (Function.owner_id == 'system'),
                                Function.disabled == '0')
                         )
        if functions is None:
            return None


        for func in functions:
            print(json.loads(func.function_detail))


        return [json.loads(func.function_detail) for func in functions]


    def __str__(self):
        return jsonpickle.encode(self, unpicklable=False)

    def to_json(self):
        return json.loads(jsonpickle.encode(self, unpicklable=False))

    def to_dict(self):
        return json.loads(jsonpickle.encode(self, unpicklable=False))

    class Meta:
        database = db
        table_name = "function"


# 如果数据库中不存在表，则创建表
db.connect()
db.create_tables([Function], safe=True)
db.close()