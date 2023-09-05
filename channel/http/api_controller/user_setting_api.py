import json

from flask import jsonify
from flask import request, Blueprint

from channel.http import auth
from common.error_code import ErrorCode, HTTPStatusCode
from common.log import logger
from service.user_setting_service import upload_user_avatar

api = Blueprint('api', __name__)


def verify_user(request_data):
    token = json.loads(request_data.data).get('token', '')
    if token is None:
        return None
    current_user = auth.identify(token)
    return current_user


@api.route("/update_user_profile", methods=['POST'])
def update_user_profile():
    current_user = verify_user(request)
    updated_user_profile = json.loads(request.data).get('user_profile', '')
    if current_user is None:
        return jsonify({"error": "Invalid user"}), HTTPStatusCode.unauthorized

    result = update_user_profile(updated_user_profile)

    match result:
        case ErrorCode.no_information_update:
            return jsonify({"error": "There is no information to update."}), HTTPStatusCode.ok
        case ErrorCode.no_user_found:
            return jsonify({"error": "User not exist"}), HTTPStatusCode.unauthorized
        case HTTPStatusCode.ok:
            return jsonify({"message": "Update user information success"}), HTTPStatusCode.ok
