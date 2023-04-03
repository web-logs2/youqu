import logging

from common.db.document_record import DocumentRecord
from model.menu_function import MenuFunction


class DocumentList(MenuFunction):

    @staticmethod
    def getName() -> str:
        return "文档列表"

    @staticmethod
    def getDescription() -> str:
        return "#查询文档  <page index>"

    @staticmethod
    def getCmd() -> str:
        return "#文档列表"

    def execute(self, arg):
        page_number = 1
        if len(arg) >= 2:
            try:
                page_number = int(arg[1])
            except Exception as e:
                return '页码错误'
        result = '```java\n'

        documents: list[DocumentRecord] = DocumentRecord.select().where(DocumentRecord.deleted == 0).paginate(
            page_number, 50)
        logging.info("Documents size:{}".format(len(documents)))
        for row in documents:
            result += "文件名： " + row.title + " 训练 :"
            result += "已完成" if row.trained else "未完成"
            result += '\n\n'
        return result

    def getOrder(self) -> int:
        return 1
