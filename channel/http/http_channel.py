# encoding:utf-8
import asyncio
import base64
import datetime
import json
import os
import time

import geoip2
import nest_asyncio
from flask import Flask, request, render_template, make_response
from flask import jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from geoip2 import database
from larksuiteoapi import OapiHeader
from larksuiteoapi.card import handle_card
from larksuiteoapi.event import handle_event
from larksuiteoapi.model import OapiRequest

import common.email
import config
from channel.channel import Channel
from channel.feishu.common_service import conf
from channel.http import auth
from channel.http.auth import sha256_encrypt, Auth
from common import const, log
from common.db.dbconfig import db
from common.db.query_record import QueryRecord
from common.db.user import User
from common.email import send_reset_password
from common.functions import is_valid_password, is_valid_email, is_valid_username, is_valid_phone, \
    is_path_empty_or_nonexistent
from common.generator import generate_uuid
from config import channel_conf, model_conf
from model import model_factory
from model.azure.azure_model import AZURE
from service.file_training_service import upload_file_service

nest_asyncio.apply()
http_app = Flask(__name__, template_folder='templates', static_folder='static')
# 自动重载模板文件
http_app.jinja_env.auto_reload = True
http_app.config['TEMPLATES_AUTO_RELOAD'] = True

CORS(http_app)
socketio = SocketIO(http_app, cors_allowed_origins="*")

# 设置静态文件缓存过期时间
http_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

ip_reader = geoip2.database.Reader('./resources/GeoLite2-City.mmdb');


@http_app.route("/text", methods=['POST'])
def text():
    user_id = auth.identify(request)
    if user_id is None:
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        data['uid'] = user_id
        request_type = data.get('request_type', "text")
        if not msg:
            return
        reply_text = HttpChannel().handle_text(data=data)
        # reply_text="Test reply"
        return {'content': reply_text}


@http_app.route("/voice", methods=['POST'])
def voice():
    user_id = auth.identify(request)
    if user_id is None:
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        data['uid'] = user_id
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
    user_id = auth.identify(request)
    if user_id is None:
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        data['uid'] = user_id
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
    user_id = auth.identify(request)
    if user_id is None:
        log.INFO("Cookie error")
        return
    if len(request.files) <= 0:
        return jsonify({'content': 'No file selected'})

    file = request.files['files']
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'content': 'No file selected'})
    return upload_file_service(file, user_id)


@http_app.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@http_app.route('/register', methods=['POST'])
def register():
    data = json.loads(request.data)
    email = data.get('email', '')
    password = data.get('password', '')
    username = data.get('username', '')
    phone = data.get('phone', '')

    if not (is_valid_email(email) and is_valid_password(password) and is_valid_username(username) and is_valid_phone(
            phone)):
        return jsonify({"error": "Invalid input format"}), 400

    if User.select().where(User.email == email).first() is not None:
        return jsonify({"error": "Email already exists"}), 400

    new_user = User(user_id=generate_uuid(), user_name=username, email=email, phone=phone,
                    password=sha256_encrypt(password), last_login=datetime.datetime.now(),
                    created_time=datetime.datetime.now(),
                    updated_time=datetime.datetime.now())
    new_user.save()
    token = Auth.encode_auth_token(new_user.user_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    log.info("Registration success: " + new_user.email)
    return jsonify({"content": "success", "username": new_user.user_name, "token": token}), 200


##sign out
@http_app.route("/sign-out", methods=['POST'])
def sign_out():
    user_id = auth.identify(request)
    model_factory.create_bot(config.conf().get("model").get("type")).clear_session_by_user_id(user_id)
    log.info("Login out: ")
    return jsonify({"content": "success"})


@http_app.route("/login", methods=['POST'])
def login():
    data = json.loads(request.data)
    password = data.get('password', '')
    email = data.get('email', '')
    current_user = auth.authenticate(email, password)
    if current_user is None:
        return jsonify({"error": "Invalid email or password"}), 200
    else:
        # add current user to session
        #        session['user'] = current_user
        token = Auth.encode_auth_token(current_user.user_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        log.info("Login success: " + current_user.email)
        return jsonify({"content": "success", "username": current_user.user_name, "token": token}), 200


@http_app.route("/sendcode", methods=['POST'])
def send_code():
    data = json.loads(request.data)
    email = data.get('email', '')
    current_user = User.select().where(User.email == email).first()
    if current_user is None:
        return jsonify({"content": "Reset password email sent"}), 200
    reset_token = Auth.encode_auth_token(current_user.user_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 1)
    # reset_url = f'{channel_conf(const.HTTP).get("domain_name")}={reset_token}'
    common.email.send_reset_password(reset_token, email)
    return jsonify({"message": "Reset password email sent"}), 200


@http_app.route("/reset_password", methods=['POST'])
def reset_password():
    user_id = auth.identify(request)
    if user_id is None:
        return jsonify({"error": "Invalid token"}), 401
    data = json.loads(request.data)
    password = data.get('password', '')
    if not is_valid_password(password):
        return jsonify({"error": "Invalid password"}), 400  # bad request
    current_user = User.select().where(User.user_id == user_id).first()
    current_user.password = sha256_encrypt(password)
    current_user.updated_time = datetime.datetime.now()
    current_user.save()
    return jsonify({"message": "Reset password success"}), 200


@http_app.route("/get_user_info", methods=['POST'])
def get_user_info():
    user_id = auth.identify(request)
    current_user = User.select().where(User.user_id == user_id).first()
    if current_user is None:
        return jsonify({"error": "Invalid user"}), 401
    return jsonify({"email": current_user.email, "username": current_user.user_name, "phone": current_user.phone}), 200


@http_app.teardown_request
def teardown_request(exception):
    db.close()


async def return_stream(data):
    last_emit_time = time.time()
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
                current_time = time.time()
                if current_time - last_emit_time >= 2:
                    socketio.sleep(0.001)
                    socketio.server.emit(
                        'reply',
                        {'content': response, 'messageID': data['messageID'],
                         'conversation_id': data['conversation_id'],
                         'final': final}, request.sid,
                        namespace="/chat")
                    last_emit_time = current_time
            # disconnect()
    except Exception as e:
        disconnect()
        log.error("[http]emit:{}", e)


@socketio.on('message', namespace='/chat')
def stream(data):
    user_id = auth.identify(request, True)
    if user_id is None:
        log.info("Cookie error")
        socketio.emit('logout', {'error': "invalid cookie"}, namespace='/chat')
    # data = json.loads(data)
    data['uid'] = user_id
    log.info("message:" + data['msg'])
    if data:
        asyncio.run(return_stream(data))


@socketio.on('connect', namespace='/chat')
def connect():
    user_id = auth.identify(request, True)
    if user_id is None:
        log.info("Cookie error")
        socketio.emit('logout', {'error': "invalid cookie"}, namespace='/chat')
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
        ip = request.remote_addr
        ip_location = ""
        try:
            ip_location = ip_reader.city(ip)
        except Exception as e:
            log.error("[http]ip:{}", e)

        query_record = QueryRecord(
            user_id=context['from_user_id'],
            conversation_id=context['conversation_id'],
            query=data["msg"],
            reply="",
            ip=ip,
            ip_location=ip_location,
            created_time=datetime.datetime.now(),
            updated_time=datetime.datetime.now(),
        )
        query_record.save()

        async for final, reply in super().build_reply_stream(data["msg"], context):
            if final:
                query_record.reply = reply
                query_record.save()
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
