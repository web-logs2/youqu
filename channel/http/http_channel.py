# encoding:utf-8
import base64
import json
import os

import nest_asyncio
from flask_socketio import SocketIO
from flask import Flask, request, render_template, make_response
from flask import jsonify
from flask_cors import CORS
from larksuiteoapi import OapiHeader
from larksuiteoapi.card import handle_card
from larksuiteoapi.event import handle_event
from larksuiteoapi.model import OapiRequest
from channel.channel import Channel
from channel.http import auth
from common import const, log
from common.generator import generate_uuid
from config import channel_conf, model_conf
from model.azure.azure_model import AZURE
from channel.feishu.common_service import conf
from service.file_training_service import upload_file_service
from common.db.dbconfig import db
import asyncio

nest_asyncio.apply()
http_app = Flask(__name__, template_folder='templates', static_folder='static')
# 自动重载模板文件
http_app.jinja_env.auto_reload = True
http_app.config['TEMPLATES_AUTO_RELOAD'] = True

CORS(http_app)
socketio = SocketIO(http_app, cors_allowed_origins="*")

# 设置静态文件缓存过期时间
http_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@http_app.route("/text", methods=['POST'])
def text():
    if not auth.identify(request):
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        request_type = data.get('request_type', "text")
        if not msg:
            return
        reply_text = HttpChannel().handle_text(data=data)
        # reply_text="Test reply"
        return {'content': reply_text}


@http_app.route("/voice", methods=['POST'])
def voice():
    if not auth.identify(request):
        log.info("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        request_type = data.get('request_type', "text")
        if not msg:
            return
        reply_text = HttpChannel().handle_text(data=data)
        azure = AZURE()
        audio_data = azure.synthesize_speech(reply_text).audio_data
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        response = {
            "audio_data": audio_base64,
            "result": reply_text,
        }
        return jsonify(response)


@http_app.route("/picture", methods=['POST'])
def picture():
    if not auth.identify(request):
        log.info("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        request_type = data.get('request_type', "text")
        if not msg:
            return
        reply_picture = HttpChannel().handle_picture(data=data)
        response = {
            "picture_data": reply_picture
        }
        return jsonify(response)


@http_app.route('/upload', methods=['POST'])
def upload_file():
    if not auth.identify(request):
        log.info("Cookie error")
        return
    # 检查文件是否存在
    if len(request.files) <= 0:
        return jsonify({'content': 'No file selected'})

    file = request.files['files']
    uid = request.form.get('uid')
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'content': 'No file selected'})
    return upload_file_service(file, uid)


@http_app.route("/", methods=['GET'])
def index():
    if (auth.identify(request) == False):
        return login()
    return render_template('index.html')


@http_app.route("/login", methods=['POST', 'GET'])
def login():
    response = make_response("<html></html>", 301)
    response.headers.add_header('content-type', 'text/plain')
    response.headers.add_header('location', './')
    if (auth.identify(request) == True):
        return response
    else:
        if request.method == "POST":
            token = auth.authenticate(request.form['password'])
            if (token != False):
                response.set_cookie(key='Authorization', value=token)
                response.set_cookie(key='id', value=generate_uuid())
                return response
        else:
            return render_template('login.html')
    response.headers.set('location', './login?err=登录失败')
    return response


@http_app.teardown_request
def teardown_request(exception):
    db.close()


def is_path_empty_or_nonexistent(path):
    if not path:
        return True
    elif not os.path.exists(path):
        return True
    elif os.path.isfile(path):
        return False
    else:
        return len(os.listdir(path)) == 0


async def return_stream(data):
    try:
        async for final, response in HttpChannel().handle_stream(data=data):
            if final:
                log.info("Final:" + response)
                socketio.server.emit(
                    'final',
                    {'content': response, 'messageID': data['messageID'], 'conversation_id': data['conversation_id'],
                     'final': final}, request.sid,
                    namespace="/chat")
                disconnect()
            else:
                # log.info("reply:" + response)
                socketio.sleep(0.001)
                socketio.server.emit(
                    'reply',
                    {'content': response, 'messageID': data['messageID'], 'conversation_id': data['conversation_id'],
                     'final': final}, request.sid,
                    namespace="/chat")
            # disconnect()

    except Exception as e:
        disconnect()
        log.warning("[http]emit:{}", e)


@socketio.on('message', namespace='/chat')
def stream(data):
    if not auth.identify(request):
        disconnect()
        return
    # data = json.loads(data)
    log.info("message:" + data['msg'])
    if data:
        asyncio.run(return_stream(data))


@socketio.on('connect', namespace='/chat')
def connect():
    if not auth.identify(request):
        disconnect()
        return
    log.info('connected')
    socketio.emit('connected', {'info': "connected"}, namespace='/chat')


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    log.info('disconnect')
    socketio.server.disconnect(request.sid, namespace="/chat")
    db.close()


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

    def handle_text(self, data, stream=False):
        context = dict()
        context['from_user_id'] = str(data["uid"])
        context['conversation_id'] = str(data["conversation_id"])
        return super().build_text_reply_content(data["msg"], context)

    async def handle_stream(self, data):
        context = dict()
        context['from_user_id'] = str(data["uid"])
        context['conversation_id'] = str(data["conversation_id"])
        context['system_prompt'] = str(data.get("system_prompt", model_conf(const.OPEN_AI).get("character_desc", "")))
        if context['system_prompt'] == "":
            context['system_prompt'] = model_conf(const.OPEN_AI).get("character_desc", "")
        log.info("Handle stream:" + data["msg"])
        async for final, reply in super().build_reply_stream(data["msg"], context):
            yield final, reply

    def handle_picture(self, data):
        context = dict()
        id = data["uid"]
        context['from_user_id'] = str(id)
        return super().build_picture_reply_content(data["msg"])


@http_app.route('/webhook/card', methods=['POST'])
def webhook_card():
    log.info("/webhook/card:" + request.data.decode())
    oapi_request = OapiRequest(uri=request.path, body=request.data, header=OapiHeader(request.headers))
    resp = make_response()
    oapi_resp = handle_card(conf, oapi_request)
    resp.headers['Content-Type'] = oapi_resp.content_type
    resp.data = oapi_resp.body
    resp.status_code = oapi_resp.status_code
    return resp


@http_app.route('/webhook/event', methods=['GET', 'POST'])
def webhook_event():
    log.info("/webhook/event:" + request.data.decode())
    oapi_request = OapiRequest(uri=request.path, body=request.data, header=OapiHeader(request.headers))
    resp = make_response()
    oapi_resp = handle_event(conf, oapi_request)
    resp.headers['Content-Type'] = oapi_resp.content_type
    resp.data = oapi_resp.body
    resp.status_code = oapi_resp.status_code
    return resp
