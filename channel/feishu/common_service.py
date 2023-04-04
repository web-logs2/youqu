import logging
from typing import Any, Union, Dict

from larksuiteoapi import Config, Context, DOMAIN_FEISHU, DefaultLogger, LEVEL_DEBUG, LEVEL_INFO

from larksuiteoapi.card import Card, set_card_callback, handle_card
from larksuiteoapi.event import set_event_callback

from larksuiteoapi.model import OapiHeader, OapiRequest

from flask import Flask, request
from flask.helpers import make_response

# 企业自建应用的配置
# AppID、AppSecret: "开发者后台" -> "凭证与基础信息" -> 应用凭证（AppID、AppSecret）
# VerificationToken、EncryptKey："开发者后台" -> "事件订阅" -> 事件订阅（VerificationToken、EncryptKey）
# 更多可选配置，请看：README.zh.md->如何构建应用配置（AppSettings）。
import config

app_id = config.feishu_conf("app_id")
app_secret = config.feishu_conf("app_secret")
verification_token = config.feishu_conf("verification_token")
encrypt_key = config.feishu_conf("encrypt_key")

app_settings = Config.new_internal_app_settings(app_id=app_id, app_secret=app_secret,
                                                verification_token=verification_token, encrypt_key=encrypt_key)

# 当前访问的是飞书，使用默认存储、默认日志（Error级别），更多可选配置，请看：README.zh.md->如何构建整体配置（Config）。
conf = Config(DOMAIN_FEISHU, app_settings, log_level=LEVEL_INFO)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
