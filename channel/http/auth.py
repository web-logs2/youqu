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
    def encode_auth_token(user_id, login_time, expire=24):
        """
        生成认证Token
        :param user_id: int
        :param login_time: datetime
        :return: string
        """
        try:
            payload = {
                'iss': 'ken',  # 签名
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=expire),  # 过期时间
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
                'http_auth_secret_key'), algorithms='HS256',
                                 options={'verify_exp': False})  # options={'verify_exp': False} 加上后不验证token过期时间
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


def identify(token: str) -> User:
    """
    用户鉴权
    :return: list
    """
    # if project_conf("env") == "development":
    #     return True
    try:
        if token:
            payload = Auth.decode_auth_token(token)
            if not isinstance(payload, str):
                current_user = User.select().where(User.user_id == payload['data']['id'], User.deleted != 1).first()
                if current_user is None:
                    log.info("User not found:{}", payload['data']['id'])
                    return None
                else:
                    current_user.last_login = datetime.datetime.now()
                    current_user.save()
                    # current_user.save_in_session()
                    return current_user
            else:
                log.info("Token error: {}", payload)
        return None

    except jwt.ExpiredSignatureError:
        log.info("Token expired {}", token)
        # result = 'Token已更改，请重新登录获取'
        return None

    except jwt.InvalidTokenError:
        log.info("Invalid token {}", token)
        # result = '没有提供认证token'
        return None


def identify_token(token: str):
    try:
        if token:
            payload = Auth.decode_auth_token(token)
            if not isinstance(payload, str):
                return payload['data']['id']
            log.info("Token error: {}", payload)
            return None

    except jwt.ExpiredSignatureError:
        log.info("Token expired {}", token)
        # result = 'Token已更改，请重新登录获取'
        return None

    except jwt.InvalidTokenError:
        log.info("Invalid token {}", token)
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
    # login_user= User.select().where(User.email == email and User.password).first()
    current_user = User.select().where((User.email == email) & (User.password == sha256_encrypt(password))).first()
    if current_user is None:
        return
    else:
        return current_user
