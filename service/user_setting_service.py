import datetime
import os
from pathlib import Path

from channel.http.auth import sha256_encrypt
from common.db.user import User
from common.error_code import ErrorCode, HTTPStatusCode
from config import project_conf


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
    try:
        filename = file.filename
        # could add verify file logic here
    except Exception as e:
        return ErrorCode.file_invalid

    # save path with user id
    folder_path = project_conf("upload_customer_avatar_folder") + Path(user.user_id).stem + "/"
    upload_avatar_dir = "./" + folder_path

    file_path = os.path.join(upload_avatar_dir, filename)

    try:
        # check if file exist
        if os.path.exists(file_path):
            return ErrorCode.file_exist
        # create dir if not exist
        if not os.path.exists(upload_avatar_dir):
            os.makedirs(upload_avatar_dir)
        # save file
        file.save(file_path)
        url = os.path.join(project_conf("endpoint"), "cdn", Path(user.user_id).stem, filename)
        return url
    except Exception as e:
        return ErrorCode.IO_operation_error
