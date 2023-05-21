# encoding:utf-8

import datetime
import hashlib
import json

import jsonpickle
import jwt
from flask import session

from common import const, log
from common.db.user import User
from config import channel_conf


class Auth:
    def __init__(self, login):
        # argument 'privilegeRequired' is to set up your method's privilege
        # name
        self.login = login
        super(Auth, self).__init__()

    @staticmethod
    def encode_auth_token(user_id, login_time):
        """
        生成认证Token
        :param user_id: int
        :param login_time: datetime
        :return: string
        """
        try:
            payload = {
                'iss': 'ken',  # 签名
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=24),  # 过期时间
                'iat': datetime.datetime.utcnow(),  # 开始时间
                'data': {
                    'id': user_id,
                    'login_time': login_time
                }
            }
            return jwt.encode(
                payload,
                channel_conf(const.HTTP).get('http_auth_secret_key'),
                algorithm='HS256'
            )  # 加密生成字符串
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        验证Token
        :param auth_token:
        :return: integer|string
        """
        try:
            # 取消过期时间验证
            payload = jwt.decode(auth_token, channel_conf(const.HTTP).get(
                'http_auth_secret_key'), algorithms='HS256')  # options={'verify_exp': False} 加上后不验证token过期时间
            if 'data' in payload and 'id' in payload['data']:
                return payload
            else:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return 'Token过期'
        except jwt.InvalidTokenError:
            return '无效Token'


def sha256_encrypt(password):
    return hashlib.sha256(password.encode()).hexdigest()


def identify(request, is_stream=False):
    """
    用户鉴权
    :return: list
    """
    # if project_conf("env") == "development":
    #     return True

    try:
        if request is None:
            log.info("Request is none")
            return None
        if is_stream:
            token = request.args.get('token')
        else:
            token = json.loads(request.data).get('token', '')
        if token:
            payload = Auth.decode_auth_token(token)
            if not isinstance(payload, str):
                current_user = User.select().where(User.id == payload['data']['id'] and User.deleted != 1).first()
                if current_user is None:
                    return None
                else:
                    current_user.last_login = datetime.datetime.now()
                    current_user.save()
                    current_user.save_in_session()
                    return payload['data']['id']
            else:
                log.info("Token error: {}", payload)
        return None

    except jwt.ExpiredSignatureError:
        # result = 'Token已更改，请重新登录获取'
        return None

    except jwt.InvalidTokenError:
        # result = '没有提供认证token'
        return None


# def authenticate(password):
#     """
#     用户登录，登录成功返回token
#     :param password:
#     :return: json
#     """
#     authPassword = channel_conf(const.HTTP).get('http_auth_password')
#     if authPassword != password:
#         return False
#     else:
#         login_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#         token = Auth.encode_auth_token(password, login_time)
#         return token

def authenticate(email, password) -> User:
    if password == '' or email == '':
        return
    current_user = User.select().where(User.email == email and User.password == sha256_encrypt(password)).first()
    if current_user is None:
        return
    else:
        return current_user
