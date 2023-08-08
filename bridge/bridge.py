import config
from model import model_factory
from common.menu_functions.menu_function import MenuFunction


class Bridge(object):
    def __init__(self):
        pass

    def fetch_text_reply_content(self, context):
        return model_factory.create_bot(config.conf().get("model").get("type")).reply(context)

    def fetch_picture_reply_content(self, context):
        return model_factory.create_bot(config.conf().get("model").get("picture")).create_img(context)

    def fetch_menu_list(self) -> MenuFunction:
        return model_factory.create_bot(config.conf().get("model").get("type")).menuList(self)

    async def fetch_reply_stream(self, context):
        bot = model_factory.create_bot(config.conf().get("model").get("type"))
        async for final, response in bot.reply_text_stream(context):
            yield final, response
