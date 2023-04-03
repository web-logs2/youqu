from concurrent.futures import ThreadPoolExecutor

import werobot

from channel.channel import Channel
from common import const
from common.log import logger
from config import channel_conf

robot = werobot.WeRoBot(token=channel_conf(const.WECHAT_MP).get('token'))
thread_pool = ThreadPoolExecutor(max_workers=8)


@robot.text
def hello_world(msg):
    logger.info('[WX_Public] receive public msg: {}, userId: {}'.format(msg.content, msg.source))
    return WechatServiceAccount().handle_text(msg)


class WechatServiceAccount(Channel):
    def startup(self):
        logger.info('[WX_Public] Wechat Public account service start!')
        robot.config['PORT'] = channel_conf(const.WECHAT_MP).get('port')
        robot.config["APP_ID"] = channel_conf(const.WECHAT_MP).get('app_id')
        robot.config["APP_SECRET"] = channel_conf(const.WECHAT_MP).get('app_secret')
        robot.config['HOST'] = '0.0.0.0'
        robot.run()

    def handle_text(self, msg, count=0):
        context = {}
        context['from_user_id'] = msg.source
        thread_pool.submit(self._do_send, msg.content, context)
        return "正在思考中..."

    def _do_send(self, query, context):
        reply_text = super().build_text_reply_content(query, context)
        logger.info('[WX_Public] reply content: {}'.format(reply_text))
        client = robot.client
        client.send_text_message(context['from_user_id'], reply_text)
