import logging
import os
import time
import dbutils

from llama_index import GPTSimpleVectorIndex
from llama_index.optimization import SentenceEmbeddingOptimizer

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from model.menu_function import MenuFunction

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class QueryDcoumnet(MenuFunction):

    def getName(self) -> str:
        return "阅读书籍"

    def getDescription(self) -> str:
        return "#阅读书籍  <书籍>  <query>"

    def getCmd(self) -> str:
        return "#阅读书籍"

    def execute(self, arg) -> any:
        if (len(arg) <= 2):
            return "请输入需要阅读的书籍和问题"
        try:
            with dbutils.atomic():
              records = DocumentRecord.select().where(DocumentRecord.title == arg[1])
              if (records.count() <= 0):
                  return '书籍不存在'
              if (records[0].trained == False):
                  return '书籍未训练完成'
              index = GPTSimpleVectorIndex.load_from_disk(records[0].trained_file_path)

              start_time = time.time()
              res = index.query(arg[2],
                                optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7))
              end_time = time.time()
              logging.info("Total time elapsed: {}".format(end_time - start_time))
              logging.info("Answer: {}".format(res.response))

              return res.response
        except Exception as e:
            log.exception(e)
            return '读取失败，请重试'

    def getOrder(self) -> int:
        return 3
