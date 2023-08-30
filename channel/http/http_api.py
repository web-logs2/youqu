# encoding:utf-8
import base64
import datetime
import hashlib
import io
import json
import time

from flask import jsonify, send_file
from flask import request, render_template, make_response, session, redirect, Blueprint
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
from common import log
from common.const import MODEL_GPT_35_turbo_16K, BOT_SYSTEM_PROMPT
from common.db.dbconfig import db
from common.db.document_record import DocumentRecord
from common.db.function import Function
from common.db.prompt import Prompt
from common.db.user import User
from common.functions import is_valid_password, is_valid_email, is_valid_username, is_valid_phone
from common.generator import generate_uuid
from common.log import logger
from model import model_factory
from model.azure.azure_model import AZURE
from service.file_training_service import upload_file_service
from service.payment import sign_lantu_payment

api = Blueprint('api', __name__)
# azure=AZURE()



@api.route("/bot/text", methods=['POST'])
def text():
    token = request.headers.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        response = {
            "success": False,
            "error": "invalid token",
            "code": "0000001",
        }
        return jsonify(response)
    data = json.loads(request.data)
    if data:
        msg = data.get("msg", ""),
        if not msg:
            response = {
                "success": False,
                "error": "您没有输入有效的问题",
                "code": "0000003",
            }
            return response
        data['uid'] = user.user_id
        data['request_type'] = "text"
        data['response_type'] = "text"
        data['conversation_id'] = user.user_id
        data['messageID'] = generate_uuid()
        data['model']= MODEL_GPT_35_turbo_16K
        data['system_prompt'] = BOT_SYSTEM_PROMPT
        data['user']=user
        reply_text = handle_text(data=data)
        return {'content': reply_text}
    else:
        response = {
            "success": False,
            "error": "invalid input parameters",
            "code": "0000002",
        }
        return response


# @api.route("/bot/voice", methods=['POST'])
# def voice():
#     response=text()
#     if response and response["content"]:
#         reply = response["content"]
#     elif response and response["error"]:
#         reply = response["error"]
#     else:
#         reply = "未知错误"
#     logger.info("reply generated")
#     audio_data = AZURE().synthesize_speech(reply).audio_data
#     logger.info("audio_data generated")
#     return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg')






@api.route("/picture", methods=['POST'])
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
        reply_picture = handle_picture(data=data, user=user)
        response = {
            "picture_data": reply_picture
        }
        return jsonify(response)


# def verify_api(self):
#     token = request.args.get('token', '')
#     user = auth.identify(token)
#     if user is None:
#         log.info("Token error")
#         response = {
#             "success":False,
#             "error": "invalid token",
#             "code": "0000001",
#         }
#         return jsonify(response)
#     return user

# @api.route('/upload', methods=['POST'])
# def upload_file():
#     if 'token' not in request.form:
#         return jsonify({"error": "Token is missing"}), 400
#     token = request.form['token']
#     user = auth.identify(token)
#     if user is None:
#         log.info("Token error")
#         return
#     if len(request.files) <= 0:
#         return jsonify({'content': 'No file selected'}), 400
#
#     file = request.files['files']
#     # 检查文件名是否为空
#     if file.filename == '':
#         return jsonify({'content': 'No file selected'}), 400
#     return upload_file_service(file, user.user_id)


@api.route('/upload', methods=['POST'])
def upload_file():
    token = request.headers.get('Authorization')
    if token is None:
        return jsonify({"error": "Token is missing"}), 400

    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        return jsonify({"error": "Invalid token"}), 403

    if 'file' not in request.files:
        return {"error": "No file in request"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "No file selected"}, 400

    return upload_file_service(file, user)


@api.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@api.route('/register', methods=['POST'])
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
    # session["user"] = jsonpickle.encode(current_user)
    token = Auth.encode_auth_token(current_user.user_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    log.info("Registration success: " + current_user.email)
    return jsonify(
        {"content": "success", "username": current_user.user_name, "token": token, "email": current_user.email,
         "phone": current_user.phone,
         "available_models": current_user.get_available_models()}), 200


##sign out
@api.route("/sign-out", methods=['POST'])
def sign_out():
    token = json.loads(request.data).get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        return
    model_factory.create_bot(config.conf().get("model").get("type")).clear_session_by_user_id(user.user_id)
    log.info("Login out: ")
    return jsonify({"content": "success"})


@api.route("/login", methods=['POST'])
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
            {"content": "success", "username": current_user.user_name, "user_id": current_user.user_id, "token": token,
             "email": current_user.email,
             "phone": current_user.phone,
             "available_models": current_user.get_available_models()}), 200


@api.route("/login", methods=['get'])
def login_get():
    log.info("Login success: ")
    return redirect('/#/login')


@api.route("/sendcode", methods=['POST'])
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


@api.route("/reset_password", methods=['POST'])
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


@api.route("/get_user_info", methods=['POST'])
def get_user_info():
    token = json.loads(request.data).get('token', '')
    current_user = auth.identify(token)
    if current_user is None:
        return jsonify({"error": "Invalid user"}), 401
    available_prompts = Prompt.get_available_prompts(current_user.user_id)
    available_functions= Function.get_available_functions(current_user.user_id)
    return jsonify({"username": current_user.user_name, "user_id": current_user.user_id, "email": current_user.email,
                    "phone": current_user.phone,
                    "available_models": current_user.get_available_models(),
                    "available_documents": DocumentRecord.query_all_available_documents(current_user.user_id),
                    "available_prompts": available_prompts,
                    "available_functions": available_functions
                    }), 200


@api.teardown_request
def teardown_request(exception):
    db.close()



# @api.before_request
# def log_request_info():
#     logger.info('Headers: %s' % request.headers)
#     logger.info('Body: %s' % request.get_data())


@api.route("/api/payment/notify", methods=['POST'])
def handle_payment_notify():

    # 获取请求数据
    data = request.form.to_dict()
    logger.info("data:{}".format(data))
    # 验证签名
    sign = data.pop('sign', '')
    sorted_data = sorted(data.items(), key=lambda x: x[0], reverse=False)
    # sign_str = "&".join(["{}={}".format(k, v) for k, v in sorted_data]) + '&key=' + MERCHANT_KEY
    if sign_lantu_payment(data) != sign:
        return 'FAIL'

    # 检查支付结果并处理业务逻辑
    if data['code'] == '0':
        out_trade_no = data['out_trade_no']
        logger.info("out_trade_no:{}".format(out_trade_no))
        # 这里添加你的业务代码，例如更新订单状态，记得处理重复通知的情况
        pass
    else:
        return 'FAIL'

    return 'SUCCESS'

# @api.route('/webhook/card', methods=['POST'])
# def webhook_card():
#     log.info("/webhook/card:" + request.data.decode())
#     oapi_request = OapiRequest(uri=request.path, body=request.data, header=OapiHeader(request.headers))
#     resp = make_response()
#     oapi_resp = handle_card(conf, oapi_request)
#     resp.headers['Content-Type'] = oapi_resp.content_type
#     resp.data = oapi_resp.body
#     resp.status_code = oapi_resp.status_code
#     return resp
#
#
# @api.route('/webhook/event', methods=['GET', 'POST'])
# def webhook_event():
#     log.info("/webhook/event:" + request.data.decode())
#     oapi_request = OapiRequest(uri=request.path, body=request.data, header=OapiHeader(request.headers))
#     resp = make_response()
#     oapi_resp = handle_event(conf, oapi_request)
#     resp.headers['Content-Type'] = oapi_resp.content_type
#     resp.data = oapi_resp.body
#     resp.status_code = oapi_resp.status_code
#     return resp


def handle_text(data):
    return Channel.build_text_reply_content(data)


def handle_picture(self, data, user: User):
    context = dict()
    context['user'] = user
    return super().build_picture_reply_content(data["msg"])
