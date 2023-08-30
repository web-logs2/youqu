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




@api.route("/api/payment/notify", methods=['POST'])
def handle_payment_notify():

    #     支付通知API
    # 蓝兔支付通过支付通知接口将用户支付成功消息通知给商户
    # 注意：
    #
    # 同样的通知可能会多次发送给商户系统。商户系统必须能够正确处理重复的通知。 推荐的做法是，当商户系统收到通知进行处理时，先检查对应业务数据的状态，并判断该通知是否已经处理。如果未处理，则再进行处理；如果已处理，则直接返回结果成功。在对业务数据进行状态检查和处理之前，要采用数据锁进行并发控制，以避免函数重入造成的数据混乱。
    # 如果在所有通知频率后没有收到蓝兔支付侧回调，商户应调用查询订单接口确认订单状态。
    # 特别提醒：商户系统对于开启结果通知的内容一定要做签名验证，并校验通知的信息是否与商户侧的信息一致，防止数据泄露导致出现“假通知”，造成资金损失。
    #
    # 接口说明
    # 适用对象：个人、个体户、企业
    #
    # 请求方式：POST
    #
    # 回调URL：该链接是通过支付接口中的请求参数“notify_url”来设置的，要求必须为http或https地址。请确保回调URL是外部可正常访问的，且不能携带后缀参数，否则可能导致商户无法接收到蓝兔支付的回调通知信息。回调URL示例：“https://pay.weixin.qq.com/wxpay/pay.action”
    #
    # 通知规则
    # 用户支付完成后，蓝兔支付会把相关支付结果和用户信息发送给商户，商户需要接收处理该消息，并返回应答。
    #
    # 对后台通知交互时，如果蓝兔支付收到商户的应答不符合规范或超时，蓝兔支付认为通知失败，蓝兔支付会通过一定的策略定期重新发起通知，尽可能提高通知的成功率，但蓝兔支付不保证通知最终能成功。（通知频率为15s/15s/30s/3m/10m/20m/30m/30m/30m/60m/3h/3h/3h/6h/6h - 总计 24h4m）
    #
    # 通知参数
    # 参数名	参数类型	是否参与签名	描述
    # code	String	是	支付结果，枚举值：
    # 0：成功
    # 1：失败
    # 示例值：0
    # timestamp	String	是	时间戳
    # 示例值：1669518774
    # mch_id	String	是	商户号
    # 示例值：1230000109
    # order_no	String	是	系统订单号
    # 示例值：WX202211221155084844072633
    # out_trade_no	String	是	商户订单号
    # 示例值：LTZF2022112264463
    # pay_no	String	是	支付宝或微信支付订单号
    # 示例值：4200001635202211222291508463
    # total_fee	String	是	支付金额
    # 示例值：0.01
    # sign	String	否	签名，签名验证的算法请参考《签名算法》。
    # 示例值：575225E549B2FBB82FB23505263633CD
    # pay_channel	String	否	支付渠道，枚举值：
    # alipay：支付宝
    # wxpay：微信支付
    # 示例值：wxpay
    # trade_type	String	否	支付类型，枚举值：
    # NATIVE：扫码支付
    # H5：H5支付
    # APP：APP支付
    # JSAPI：公众号支付
    # MINIPROGRAM：小程序支付
    # 示例值：NATIVE
    # success_time	String	否	支付完成时间
    # 示例值：2022-11-22 11:55:42
    # attach	String	否	附加数据，在支付接口中填写的数据，可作为自定义参数使用。
    # 示例值：自定义数据
    # openid	String	否	支付者信息
    # 示例值：o5wq46GAKVxVKpsdcI4aU4cBpgT0
    # 通知应答
    # 接收成功：HTTP应答状态码需返回200，同时应答报文需返回：SUCCESS，必须为大写。
    #
    # 接收失败：应答报文返回：FAIL。
    #请基于以上文档帮我开发这个函数


    # 获取请求数据
    data = request.get_json()

    # 验证签名
    sign = data.pop('sign', '')
    sorted_data = sorted(data.items(), key=lambda x: x[0], reverse=False)
    # sign_str = "&".join(["{}={}".format(k, v) for k, v in sorted_data]) + '&key=' + MERCHANT_KEY
    if sign_lantu_payment(sorted(data.items(), key=lambda x: x[0], reverse=False)) != sign:
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
