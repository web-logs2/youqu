import json

from flask import jsonify
from flask import request, Blueprint

from channel.http import auth
from common.error_code import ErrorCode, HTTPStatusCode
from common.log import logger
from service import user_setting_service
from service.user_setting_service import upload_user_avatar

user_api = Blueprint('user', __name__, url_prefix='/user')


def verify_user(data):
    token = data.get('token', '')
    if token == '':
        return None
    current_user = auth.identify(token)
    return current_user


@user_api.route("/update_user_profile", methods=['POST'])
def update_user_profile():
    data = json.loads(request.data)
    current_user = verify_user(data)
    updated_user_profile = data.get('user_profile', '')
    if current_user is None:
        return jsonify({"error": "Invalid user"}), HTTPStatusCode.unauthorized

    result = user_setting_service.update_user_profile(updated_user_profile)

    # match result:
    #     case ErrorCode.no_information_update:
    #         return jsonify({"error": "There is no information to update."}), HTTPStatusCode.ok.value
    #     case ErrorCode.no_user_found:
    #         return jsonify({"error": "User not exist"}), HTTPStatusCode.unauthorized.value
    #     case HTTPStatusCode.ok:
    #         return jsonify({"message": "Update user information success"}), HTTPStatusCode.ok.value


# @user_api.route("/upload_user_avatar", methods=['POST'])
def upload_user_avatar():
    user_setting_service.upload_user_avatar()
