import logging
import os
import time

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from common.menu_functions.menu_function import MenuFunction
from common.menu_functions.public_train_methods import public_query_documents

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class WxQueryDocument(MenuFunction):

    def getName(self) -> str:
        return "微信公众号"

    def getDescription(self) -> str:
        return "#微信公众号  <name>  <query>"

    def getCmd(self) -> str:
        return "#微信公众号"

    def execute(self, arg) -> any:
        if (len(arg) <= 2):
            return "请输入微信公众号和问题"
        try:
            authorName = arg[1]

            # #微信公众号 字节跳动技术团队 讲了一些什么内容

            author = DocumentRecord.select().where((DocumentRecord.title == authorName) & (DocumentRecord.type == "wx"))
            if (author.count() <= 0):
                return '微信公众号不存在'
            if (author[0].trained == False):
                return '微信公众号未训练完成'

            index_path = author[0].trained_file_path

            # index = GPTSimpleVectorIndex.load_from_disk(index_path)

            start_time = time.time()
            # res = index.query(arg[2], optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7))
            res = public_query_documents(index_path, arg[2])
            end_time = time.time()
            logging.info("Total time elapsed: {}".format(end_time - start_time))
            logging.info("Answer: {}".format(res.response))

            return res.response
        except Exception as e:
            log.exception(e)
            return '读取失败，请重试'

    def getOrder(self) -> int:
        return 6
