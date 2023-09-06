import datetime

from flask import jsonify

from channel.http.auth import sha256_encrypt
from common.db.user import User
from common.error_code import ErrorCode, HTTPStatusCode


def update_user_profile(user_profile):
    # user_profile = User.from_dict(user)
    user_id = user_profile.get('user_id')

    current_user = User.select().where((User.user_id == user_id)).first()

    # can't find user id
    if current_user is None:
        return ErrorCode.no_user_found

    is_updated = False

    # field validations
    fields_to_update = {
        'user_name': user_profile.get('name'),
        'email': user_profile.get('email'),
        'phone': user_profile.get('phone'),
        'avatar': user_profile.get('avatar'),
        'password': sha256_encrypt(user_profile.get('password')) if user_profile.get('password') is not None else None
    }
    for field, value in fields_to_update.items():
        if value is not None and value != getattr(current_user, field):
            setattr(current_user, field, value)
            is_updated = True

    # if user_profile.user_name != current_user.user_name:
    #     updated_user.user_name = user_profile.user_name
    #     is_updated = True
    # if user_profile.email != current_user.email:
    #     updated_user.email = user_profile.email
    #     is_updated = True
    # if user_profile.phone != current_user.phone:
    #     updated_user.phone = user_profile.phone
    #     is_updated = True
    # if user_profile.avatar != current_user.avatar:
    #     updated_user.avatar = user_profile.avatar
    #     is_updated = True
    # if user_profile.password is not None and sha256_encrypt(user_profile.password) != current_user.passwrod:
    #     updated_user.password = sha256_encrypt(user_profile.password)
    #     is_updated = True

    # need to update, set id and updated time
    if is_updated:
        current_user.updated_time = datetime.datetime.now()
    else:
        return ErrorCode.no_information_update

    if current_user.save():
        return HTTPStatusCode.ok
    else:
        return ErrorCode.database_operation_error


def upload_user_avatar(file, user):
    pass
