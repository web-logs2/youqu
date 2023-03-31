from common.db.document_record import DocumentRecord
from model.menu_function import MenuFunction
from llama_index import GPTSimpleVectorIndex, SimpleDirectoryReader
from common import log
from common import const
import os
from config import model_conf
os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class QueryDcoumnet(MenuFunction):
    
    def getName(self) -> str:
        return "阅读书籍"
  
    def getDescription(self)-> str:
        return "#阅读书籍  <书籍>  <query>"
    
    def getCmd(self)-> str:
        return "#阅读书籍"
    
    def excetu(self, arg)-> any:
        if(len(arg) <= 2):
            return "请输入需要阅读的书籍和问题"
        try:
            records = DocumentRecord.select().where(DocumentRecord.title == arg[1])
            if(records.count() <= 0):
                return '书籍不存在'
            if(records[0].trained == False):
                return '书籍未训练完成'
            index = GPTSimpleVectorIndex.load_from_disk(records[0].path+ '/train')
            reponse = index.query(arg[2])
            return reponse.source_nodes[0].source_text
        except Exception as e:
            log.exception(e)
            return '读取失败，请重试'
        
    def getOrder(self)-> int:
        return 2   