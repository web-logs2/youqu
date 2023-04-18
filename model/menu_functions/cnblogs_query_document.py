import logging
import os
import time
import urllib

from llama_index import GPTSimpleVectorIndex
from llama_index.optimization import SentenceEmbeddingOptimizer

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from model.menu_functions.menu_function import MenuFunction

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class CnblogsQueryDcoumnet(MenuFunction):

    def getName(self) -> str:
        return "博客园"

    def getDescription(self) -> str:
        return "#博客园  <url>  <query>"

    def getCmd(self) -> str:
        return "#博客园"

    def execute(self, arg) -> any:
        if (len(arg) <= 2):
            return "请输入博客园地址和问题"
        try:
            url = arg[1]

            # #博客园 https://www.cnblogs.com/wuxinqiu/ 讲了一些什么内容
            # #博客园 wuxinqiu 讲了一些什么内容

            if url.startswith("http"):
                urlparse = urllib.parse.urlparse(url)
                authorName = urlparse.path.replace("/", "")
            else:
                authorName = url

            author = DocumentRecord.select().where((DocumentRecord.title == authorName) & (DocumentRecord.type == "cnblogs"))
            if (author.count() <= 0):
                return '博客园不存在'
            if (author[0].trained == False):
                return '博客园未训练完成'

            index_path = author[0].trained_file_path

            index = GPTSimpleVectorIndex.load_from_disk(index_path)

            start_time = time.time()
            res = index.query(arg[2], optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7))
            end_time = time.time()
            logging.info("Total time elapsed: {}".format(end_time - start_time))
            logging.info("Answer: {}".format(res.response))

            return res.response
        except Exception as e:
            log.exception(e)
            return '读取失败，请重试'

    def getOrder(self) -> int:
        return 4
