import config
from model import model_factory
from model.menu_function import MenuFunction


class Bridge(object):
    def __init__(self):
        pass

    def fetch_text_reply_content(self, query, context, stream=False):
        if stream:
            return model_factory.create_bot(config.conf().get("model").get("type")).reply_text_stream(query, context)
        else:
            return model_factory.create_bot(config.conf().get("model").get("type")).reply(query, context)

    def fetch_picture_reply_content(self, query):
        return model_factory.create_bot(config.conf().get("model").get("picture")).create_img(query)

    def fetch_menu_list(self) -> MenuFunction:
        return model_factory.create_bot(config.conf().get("model").get("type")).menuList(self)
