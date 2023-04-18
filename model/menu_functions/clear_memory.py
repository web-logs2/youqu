import os

from common import const, log
from config import model_conf
from model.menu_functions.menu_function import MenuFunction

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class ClearMemory(MenuFunction):

    def getName(self) -> str:
        return "清除记忆"

    def getDescription(self) -> str:
        return "#清除记忆"
    def getCmd(self) -> str:
        return "#清除记忆"

    def execute(self, arg) -> any:
        log.info("记忆已清除")
        return '记忆已清除'

    def getOrder(self) -> int:
        return 4
