import os

from flask import session

from common import const, log
from config import model_conf, config
from model import model_factory
from common.menu_functions.menu_function import MenuFunction

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class ClearMemory(MenuFunction):

    def getName(self) -> str:
        return "清除记忆"

    def getDescription(self) -> str:
        return "#清除记忆"
    def getCmd(self) -> str:
        return "#清除记忆"

    def execute(self, arg) -> any:
        model_factory.create_bot(config.conf().get("model").get("type")).clear_session_by_user_id(session['user'].user_id)
        log.info("记忆已清除")
        return '记忆已清除'

    def getOrder(self) -> int:
        return 4
