import os

from channel.channel import Channel
from channel.http.http_api import http_app
from channel.http.socketIO_api import socketio

from common import const, log
from common.functions import is_path_empty_or_nonexistent
from config import channel_conf


class HttpChannel(Channel):
    def startup(self):
        ssl_certificate_path = channel_conf(const.HTTP).get('ssl_certificate_path')
        http_app.debug = True
        port = channel_conf(const.HTTP).get('port')

        if not ssl_certificate_path:
            ssl_certificate_path = script_directory = os.path.dirname(os.path.abspath(__file__)) + "/resources"
        if is_path_empty_or_nonexistent(ssl_certificate_path):
            socketio.run(http_app, host='0.0.0.0', port=port)
            # eventlet.wsgi.server(eventlet.listen(('', port)), http_app)
            # http_app.run(host='0.0.0.0', port=channel_conf(const.HTTP).get('port'))
        else:
            cert_path = ssl_certificate_path + '/fullchain.pem'
            key_path = ssl_certificate_path + '/privkey.pem'

            log.info("Start ssl server")
            socketio.run(http_app, host='0.0.0.0', port=port, certfile=cert_path, keyfile=key_path)
