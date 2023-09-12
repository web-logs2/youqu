import os.path
from pathlib import Path

from flask import Blueprint, send_from_directory, send_file, render_template

from config import project_conf

route_api = Blueprint('route_api', __name__)

@route_api.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@route_api.route('/cdn/<path:userid>/<path:filename>', methods=['GET'])
def get_static_file(userid, filename):
    # file_path = os.path.join(project_conf("upload_customer_avatar_folder"), Path(userid).stem)
    # return send_from_directory(directory=file_path, path=filename, _root_path=os.path.abspath('./'))

    file_path = os.path.join(os.path.abspath('./'),
                             project_conf("upload_customer_avatar_folder"),
                             Path(userid).stem,
                             filename)
    return send_file(file_path)
