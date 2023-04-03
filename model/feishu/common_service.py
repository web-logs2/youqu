import logging
from typing import Any, Union, Dict

from larksuiteoapi import Config, Context, DOMAIN_FEISHU, DefaultLogger, LEVEL_DEBUG

from larksuiteoapi.card import Card, set_card_callback, handle_card

from larksuiteoapi.model import OapiHeader, OapiRequest

from flask import Flask, request
from flask.helpers import make_response

# 企业自建应用的配置
# AppID、AppSecret: "开发者后台" -> "凭证与基础信息" -> 应用凭证（AppID、AppSecret）
# VerificationToken、EncryptKey："开发者后台" -> "事件订阅" -> 事件订阅（VerificationToken、EncryptKey）
# 更多可选配置，请看：README.zh.md->如何构建应用配置（AppSettings）。
app_settings = Config.new_internal_app_settings(app_id="cli_a4a0ee7eb839500c", app_secret="vWtKJJZPCavhxEphnuCpmwu1rJPlIaTS",
                                                verification_token="NL71IjxADs7JTj59FfLTubxitI7mRxAq", encrypt_key="=E12=QY]1as./32Ju!{PjD523Mq",)

# 当前访问的是飞书，使用默认存储、默认日志（Error级别），更多可选配置，请看：README.zh.md->如何构建整体配置（Config）。
conf = Config(DOMAIN_FEISHU, app_settings, log_level=LEVEL_DEBUG)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


# 设置消息卡片的处理
# 返回值：可以为None、新的消息卡片的Json（dict）
def handle(ctx, conf, card):
    # type: (Context, Config, Card) -> Union[None, Dict]
    print('card = %s' % card)
    return {
        "config": {
            "wide_screen_mode": True
        },
        "card_link": {
            "url": "https://www.baidu.com",
            "android_url": "https://developer.android.com/",
            "ios_url": "https://developer.apple.com/",
            "pc_url": "https://www.windows.com"
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "this is header"
            }
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": "This is a very very very very very very very long text;"
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "Read"
                        },
                        "type": "default"
                    }
                ]
            }
        ]
    }


set_card_callback(conf, handle)
app = Flask(__name__)


@app.route('/webhook/card', methods=['POST'])
def webhook_card():
    oapi_request = OapiRequest(uri=request.path, body=request.data, header=OapiHeader(request.headers))
    resp = make_response()
    oapi_resp = handle_card(conf, oapi_request)
    resp.headers['Content-Type'] = oapi_resp.content_type
    resp.data = oapi_resp.body
    resp.status_code = oapi_resp.status_code
    return resp


# 设置 "开发者后台" -> "应用功能" -> "机器人" 消息卡片请求网址：https://domain/webhook/card
# startup event http server, port: 8089
if __name__ == '__main__':
    app.run(port=8089, host="0.0.0.0")
