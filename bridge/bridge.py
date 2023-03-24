from model import model_factory
import config


class Bridge(object):
    def __init__(self):
        pass

    def fetch_text_reply_content(self, query, context):
        return model_factory.create_bot(config.conf().get("model").get("type")).reply(query, context)

    def fetch_picture_reply_content(self, query):
        return model_factory.create_bot(config.conf().get("model").get("picture")).create_img(query)
