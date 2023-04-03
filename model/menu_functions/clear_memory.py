import logging
import os
import time

from llama_index import GPTSimpleVectorIndex
from llama_index.optimization import SentenceEmbeddingOptimizer

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from model.menu_function import MenuFunction
from model.openai.chatgpt_model import Session

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class ClearMemory(MenuFunction):

    def getName(self) -> str:
        return "清除记忆"

    def getDescription(self) -> str:
        return "#清除记忆"

    def getCmd(self) -> str:
        return "#清除记忆"

    def execute(self, arg) -> any:
        Session.clear_session(from_user_id)
        return '记忆已清除'

    def getOrder(self) -> int:
        return 4
