# encoding:utf-8
import asyncio
import base64
import datetime
import json
import os
import re
import time

import jsonpickle
import nest_asyncio
from flask import Flask, request, render_template, make_response, session
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
from common.functions import is_valid_password, is_valid_email, is_valid_username, is_valid_phone, \
    is_path_empty_or_nonexistent, ip_reader
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
http_app.secret_key = channel_conf(const.HTTP).get('http_app_key')  # 设置session需要的secret_key

CORS(http_app)
socketio = SocketIO(http_app, ping_timeout=5 * 60, ping_interval=30, cors_allowed_origins="*")

# 设置静态文件缓存过期时间
http_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0



@http_app.route("/text", methods=['POST'])
def text():
    user = auth.identify(request)
    if user is None:
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        data['uid'] = user.user_id
        request_type = data.get('request_type', "text")
        if not msg:
            return
        reply_text = HttpChannel().handle_text(data=data)
        # reply_text="Test reply"
        return {'content': reply_text}


@http_app.route("/voice", methods=['POST'])
def voice():
    user = auth.identify(request)
    if user is None:
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        data['uid'] = user.user_id
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
    user = auth.identify(request)
    if user is None:
        log.INFO("Cookie error")
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        data['uid'] = user.user_id
        request_type = data.get('request_type', "text")
        if not msg:
            return
        reply_picture = HttpChannel().handle_picture(data=data, user=user)
        response = {
            "picture_data": reply_picture
        }
        return jsonify(response)


@http_app.route('/upload', methods=['POST'])
def upload_file():
    if 'token' not in request.form:
        return jsonify({"error": "Token is missing"}), 400
    token = request.form['token']
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        return
    if len(request.files) <= 0:
        return jsonify({'content': 'No file selected'}), 400

    file = request.files['files']
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'content': 'No file selected'}), 400
    return upload_file_service(file, user.user_id)


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
    if User.select().where(User.phone == phone).first() is not None:
        return jsonify({"error": "Phone already exists"}), 400

    current_user = User(user_id=generate_uuid(), user_name=username, email=email, phone=phone,
                        password=sha256_encrypt(password), last_login=datetime.datetime.now(),
                        created_time=datetime.datetime.now(),
                        updated_time=datetime.datetime.now())
    current_user.save()
    session["user"] = jsonpickle.encode(current_user)
    token = Auth.encode_auth_token(current_user.user_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    log.info("Registration success: " + current_user.email)
    return jsonify(
        {"content": "success", "username": current_user.user_name, "token": token, "email": current_user.email,
         "phone": current_user.phone,
         "available_models": current_user.get_available_models()}), 200


##sign out
@http_app.route("/sign-out", methods=['POST'])
def sign_out():
    token = json.loads(request.data).get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        return
    model_factory.create_bot(config.conf().get("model").get("type")).clear_session_by_user_id(user.user_id)
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
        return jsonify(
            {"content": "success", "username": current_user.user_name, "token": token, "email": current_user.email,
             "phone": current_user.phone,
             "available_models": current_user.get_available_models()}), 200


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
    token = json.loads(request.data).get('token', '')
    current_user = auth.identify(token)
    if current_user is None:
        return jsonify({"error": "Invalid token"}), 401
    data = json.loads(request.data)
    password = data.get('password', '')
    if not is_valid_password(password):
        return jsonify({"error": "Invalid password"}), 400  # bad request
    current_user.password = sha256_encrypt(password)
    current_user.updated_time = datetime.datetime.now()
    current_user.last_login = datetime.datetime.now()
    current_user.save()
    return jsonify({"message": "Reset password success"}), 200


@http_app.route("/get_user_info", methods=['POST'])
def get_user_info():
    token = json.loads(request.data).get('token', '')
    current_user = auth.identify(token)
    if current_user is None:
        return jsonify({"error": "Invalid user"}), 401
    return jsonify({"username": current_user.user_name, "email": current_user.email,
                    "phone": current_user.phone,
                    "available_models": current_user.get_available_models()}), 200


@http_app.teardown_request
def teardown_request(exception):
    db.close()


async def return_stream(data, user: User):
    last_emit_time = time.time()
    try:
        async for final, response in HttpChannel().handle_stream(data=data, user=user):
            if final:
                log.info("Final:" + response)
                socketio.server.emit(
                    'final',
                    {'content': response, 'messageID': data['messageID'], 'conversation_id': data['conversation_id'],
                     'final': final}, request.sid,
                    namespace="/chat")
                #disconnect()
            else:
                socketio.sleep(0.001)
                socketio.server.emit(
                    'reply',
                    {'content': response, 'messageID': data['messageID'],
                     'conversation_id': data['conversation_id'],
                     'final': final}, request.sid,
                    namespace="/chat")
            # disconnect()
    except Exception as e:
        disconnect()
        log.error("[http]emit:{}", e)


@socketio.on('message', namespace='/chat')
def message(data):
    token = request.args.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        socketio.emit('logout', {'error': "invalid cookie"}, namespace='/chat')
    # data = json.loads(data)
    log.info("message:" + data['msg'])
    if data:
        asyncio.run(return_stream(data, user))


@socketio.on('connect', namespace='/chat')
def connect():
    token = request.args.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        disconnect()
        return
    log.info('{} connected', user.email)
    socketio.emit('connected', {'info': "connected"}, namespace='/chat')


@socketio.on('heartbeat', namespace='/chat')
def heart_beat(message):
    log.info("heart beat:{}", message)
    token = request.args.get('token', '')
    user_id = auth.identify_token(token)
    if user_id is None:
        log.info("Token error")
        socketio.emit('logout', {'error': "invalid cookie"}, namespace='/chat')
        disconnect()
        return
    log.info('{} heart beat', user_id)
    socketio.server.emit(
        'heartbeat',
        'pang', request.sid,
        namespace="/chat")


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    log.info('disconnect')
    time.sleep(1)
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

    def handle_text(self, data, user: User):
        context = dict()
        context['user'] = user
        context['conversation_id'] = str(data["conversation_id"])
        return super().build_text_reply_content(data["msg"], context)

    async def handle_stream(self, data, user: User):
        context = dict()
        context['conversation_id'] = str(data["conversation_id"])
        context['user'] = user
        model = str(data.get("model", const.MODEL_GPT_35_TURBO))
        if model not in user.get_available_models():
            model = const.MODEL_GPT_35_TURBO
        context['model'] = model
        system_prompt = str(data.get("system_prompt", model_conf(const.OPEN_AI).get("character_desc", "")))
        if len(re.findall(r'\w+|[\u4e00-\u9fa5]|[^a-zA-Z0-9\u4e00-\u9fa5\s]', system_prompt)) > 500:
            system_prompt = model_conf(const.OPEN_AI).get("character_desc", "")
        context['system_prompt'] = system_prompt
        # log.info("Handle stream:" + data["msg"])
        ip = request.remote_addr
        ip_location = ""
        try:
            ip_location = ip_reader.city(ip)
        except Exception as e:
            log.error("[http]ip:{}", e)

        query_record = QueryRecord(
            user_id=context['user'].user_id,
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

    def handle_picture(self, data, user: User):
        context = dict()
        context['user'] = user
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
