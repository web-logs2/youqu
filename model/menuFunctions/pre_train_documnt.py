import os

from llama_index import GPTSimpleVectorIndex, SimpleDirectoryReader

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from model.menu_function import MenuFunction

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class PreTrainDcoumnet(MenuFunction):

    def getName(self) -> str:
        return "训练书籍"

    def getDescription(self) -> str:
        return "#训练书籍  <书籍>"

    def getCmd(self) -> str:
        return "#训练书籍"

    def execute(self, arg) -> any:
        if (len(arg) <= 1):
            return "请输入需要训练的文件名"
        try:
            records = DocumentRecord.select().where(DocumentRecord.title == arg[1])
            if (records.count() <= 0):
                return '文件不存在'
            if (records[0].trained == True):
                return '文件已经训练完成'
            documents = SimpleDirectoryReader(records[0].path).load_data()
            index = GPTSimpleVectorIndex.from_documents(documents)
            # save to disk
            # records[0].trained_data = index.save_to_string()
            path = records[0].path + '/train'
            # if not os.path.exists(path):
            #   os.mkdir(path)
            index.save_to_disk(path)
            records[0].trained = True
            records[0].save()
            return '训练完成'
        except Exception as e:
            log.exception(e)
            return '训练失败，请重试'

    def getOrder(self) -> int:
        return 2
