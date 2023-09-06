import os

from llama_index import SimpleDirectoryReader

from common import const
from common import log
from common.db.document_record import DocumentRecord
from common.menu_functions.menu_function import MenuFunction
from common.menu_functions.public_train_methods import public_train_documents
from config import model_conf

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class PreTrainDcoumnet(MenuFunction):

    def getName(self) -> str:
        return "训练书籍"

    def getDescription(self) -> str:
        return "#训练书籍"

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
            # index = GPTSimpleVectorIndex.from_documents(documents)
            index = public_train_documents(documents)
            # save to disk
            # records[0].trained_data = index.save_to_string()
            records[0].trained_file_path = records[0].path + 'index_' + os.path.splitext(os.path.basename(records[0].path + records[0].title))[0] + ".json"
            # if not os.path.exists(path):
            #   os.mkdir(path)
            # index.save_to_disk(records[0].trained_file_path)
            index.storage_context.persist(persist_dir=records[0].trained_file_path)
            records[0].trained = True
            records[0].save()
            return '训练完成'
        except Exception as e:
            log.exception(e)
            return '训练失败，请重试'

    def getOrder(self) -> int:
        return 2
