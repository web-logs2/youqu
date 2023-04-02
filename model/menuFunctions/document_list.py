

from common.db.document_record import DocumentRecord
from model.menu_function import MenuFunction


class DcoumentList(MenuFunction):  
        
    def getName(self) -> str:
        return "文档列表"
    
    def getDescription(self)-> str:
        return "#查询文档  <page index>"
    
 
    def getCmd(self)-> str:
        return "#文档列表"
    
   
    def excetu(self, arg):
        page_number = 1
        if(len(arg)>= 2):
            try:
              page_number = int(arg[1])
            except  Exception as e:
              return '页码错误'
        result = '```java\n'
        documents: list[DocumentRecord] = DocumentRecord.select().where(DocumentRecord.deleted == False).paginate(page_number, 50)
        for row  in documents:
            result += "文件名： " + row.title + " 训练 :" 
            result += "已完成" if row.trained else "未完成"   
            result += '\n\n'
        return result
    
    def getOrder(self)-> int:
        return 1
