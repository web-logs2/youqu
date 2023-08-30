# encoding:utf-8

import json
import os

from common import const

config = {}


def load_config():
    global config
    root_path = os.path.dirname(os.path.abspath(__file__))
    config_path = root_path + "/config.json"
    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据config-template.json模板创建config.json文件')

    config_str = read_file(config_path)
    # 将json字符串反序列化为dict类型
    config = json.loads(config_str)
    os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')
    print("载入环节")
    print(config)
    return config


def get_root():
    return os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read()


def conf():
    return config


def model_conf(model_type):
    return config.get('model').get(model_type)


def project_conf(key):
    return config.get('project').get(key)


def feishu_conf(key):
    return config.get('feishu').get(key)


def model_conf_val(model_type, key):
    val = config.get('model').get(model_type).get(key)
    if not val:
        # common default config
        return config.get('model').get(key)
    return val


def channel_conf(channel_type):
    return config.get('channel').get(channel_type)


def channel_conf_val(channel_type, key, default=None):
    val = config.get('channel').get(channel_type).get(key)
    if not val:
        # common default config
        return config.get('channel').get(key, default)
    return val



def payment_conf(payment_type):
    return config.get('channel').get(channel_type)