import json

from flask import jsonify
from flask import request, Blueprint

from channel.http import auth
from common.error_code import ErrorCode, HTTPStatusCode
from common.log import logger
from service import user_setting_service

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

    if result == ErrorCode.no_information_update:
        return jsonify({"error": "There is no information to update."}), HTTPStatusCode.ok.value
    elif result == ErrorCode.no_user_found:
        return jsonify({"error": "User not exist"}), HTTPStatusCode.unauthorized.value
    elif result == HTTPStatusCode.ok:
        logger.info("User {} updated profile".format(current_user.user_id))
        return jsonify({"message": "Update user information success"}), HTTPStatusCode.ok.value
    else:
        return jsonify({"error": "Unknown error"}), HTTPStatusCode.internal_server_error.value


@user_api.route("/upload_user_avatar", methods=['POST'])
def upload_user_avatar():
    data = {'token': request.headers.get('Authorization')}
    current_user = verify_user(data)
    if current_user is None:
        return jsonify({"error": "Invalid user"}), HTTPStatusCode.unauthorized
    # avatar = data.get('avatar', None)
    file = request.files.get('avatar', None)
    if file is None:
        return jsonify({"error": "Invalid avatar"}), HTTPStatusCode.bad_request

    result = user_setting_service.upload_user_avatar(file, current_user)

    # if result == HTTPStatusCode.ok.value:
    if type(result) is str:
        logger.info("User upload avatar")
        return jsonify({"message": "Upload avatar succeed"}), HTTPStatusCode.ok.value
    elif result == ErrorCode.file_invalid:
        return jsonify({"error": "Invalid avatar"}), HTTPStatusCode.bad_request.value
    elif result == ErrorCode.file_exist:
        return jsonify({"error": "Avatar already exist"}), HTTPStatusCode.ok.value
    elif result == ErrorCode.IO_operation_error:
        return jsonify({"error": "Save avatar fail, please try with another avatar"}), HTTPStatusCode.internal_server_error.value
    else:
        return jsonify({"error": "Unknown error"}), HTTPStatusCode.internal_server_error.value
