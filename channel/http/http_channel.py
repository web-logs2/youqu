import os

import flask
import nest_asyncio
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO

from channel.channel import Channel
from channel.http.http_api import api
from channel.http.socketio_handler import socket_handler

from common import const, log
from common.functions import is_path_empty_or_nonexistent
from common.log import logger
from config import channel_conf

nest_asyncio.apply()
http_app = Flask(__name__, template_folder='templates', static_folder='static')
http_app.register_blueprint(api)  # 注册蓝图
socketio = SocketIO(http_app, ping_timeout=5 * 60, ping_interval=30, cors_allowed_origins="*")

# 自动重载模板文件
http_app.jinja_env.auto_reload = True
http_app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(http_app)
handler = socket_handler(socketio)
handler.register_socketio_events()  # 注册socket_handler类中的事件

# 设置静态文件缓存过期时间
http_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0



@http_app.before_request
def log_request_info():
    logger.info('url:{}'.format(request.url))
    logger.info('header:{}'.format(request.headers))
    logger.info('data:{}'.format(request.get_data()))
#
# print('Headers: %s', flask.request.headers)
#     print('Body: %s', flask.request.get_data())


class HttpChannel(Channel):
    def startup(self):
        ssl_certificate_path = channel_conf(const.HTTP).get('ssl_certificate_path')
        http_app.debug = True
        port = channel_conf(const.HTTP).get('port')

        if not ssl_certificate_path:
            ssl_certificate_path = os.path.dirname(os.path.abspath(__file__)) + "/resources"
        if is_path_empty_or_nonexistent(ssl_certificate_path):
            socketio.run(http_app, host='0.0.0.0', port=port)
            # eventlet.wsgi.server(eventlet.listen(('', port)), http_app)
            # http_app.run(host='0.0.0.0', port=channel_conf(const.HTTP).get('port'))
        else:
            cert_path = ssl_certificate_path + '/fullchain.pem'
            key_path = ssl_certificate_path + '/privkey.pem'

            log.info("Start ssl server")
            socketio.run(http_app, host='0.0.0.0', port=port, certfile=cert_path, keyfile=key_path)
