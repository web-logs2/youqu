import logging
import os
import time

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from model.menu_functions.menu_function import MenuFunction
from model.menu_functions.public_train_methods import public_query_documents

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class QueryDcoumnet(MenuFunction):

    def getName(self) -> str:
        return "阅读书籍"

    def getDescription(self) -> str:
        return "#阅读书籍  <书籍id>  <query>"

    def getCmd(self) -> str:
        return "#阅读书籍"

    def execute(self, arg) -> any:
        if (len(arg) <= 2):
            return "请输入需要阅读的书籍和问题"
        try:
            records = DocumentRecord.select().where(DocumentRecord.id == arg[1])
            if (records.count() <= 0):
                return '书籍不存在'
            if (records[0].trained == False):
                return '书籍未训练完成'
            log.info("Trained file path:"+records[0].trained_file_path)
            # index = GPTSimpleVectorIndex.load_from_disk(records[0].trained_file_path)

            start_time = time.time()

            # res = index.query(arg[2],
            #                   streaming=True,
            #                   # mode="embedding",
            #                   # response_mode="tree_summary",  # possible: default, compact, tree_summary
            #                   optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7))

            res = public_query_documents(records[0].trained_file_path, arg[2])

            # for token in res.response_gen:
            #     log.info("token:"+token)
            #     yield token

            end_time = time.time()
            logging.info("Total time elapsed: {}".format(end_time - start_time))
            # return res.response_gen
            return res.response
        except Exception as e:
            log.exception(e)
            return '读取失败，请重试'

    def getOrder(self) -> int:
        return 3
