import os
import re
import geoip2
from geoip2.errors import AddressNotFoundError


def contain_chinese(str):
    """
    判断一个字符串中是否含有中文
    """
    pattern = re.compile('[\u4e00-\u9fa5]')
    match = pattern.search(str)
    return match != None


def check_prefix(content, prefix_list):
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None


def is_valid_password(password):
    regex = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
    return re.match(regex, password) is not None


def is_valid_username(username):
    return 5 <= len(username) <= 32


def is_valid_phone(phone):
    return len(phone) == 11 and phone.isdigit()


def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None


def is_path_empty_or_nonexistent(path):
    if not path:
        return True
    elif not os.path.exists(path):
        return True
    elif os.path.isfile(path):
        return False
    else:
        return len(os.listdir(path)) == 0


ip_reader = geoip2.database.Reader('./resources/GeoLite2-City.mmdb');
def get_city_name_in_chinese(ip: str) -> str:
    try:
        response = ip_reader.city(ip)
        city_name_chinese = response.city.names.get('zh-CN', '')
        return city_name_chinese
    except (AddressNotFoundError, ValueError):
        return ""
