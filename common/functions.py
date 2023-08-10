import os
import re
import traceback
from unicodedata import normalize

import geoip2
import tiktoken
from geoip2.errors import AddressNotFoundError
import geoip2.database

from common import const, log


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
    return len(password) >= 8


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


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        log.info("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception as e:
        # log.error(traceback.format_exc())
        return 0
    if model == const.MODEL_GPT_35_TURBO or model == const.MODEL_GPT_35_turbo_16K:
        log.info("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == const.MODEL_GPT4_8K or model == const.MODEL_GPT4_32K:
        log.info("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == const.MODEL_GPT_35_TURBO_0301:
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == const.MODEL_GPT4_0314:
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    try:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except Exception as e:
        # log.error(traceback.format_exc())
        return 0


def get_max_token(model):
    if model == const.MODEL_GPT4_8K or model == const.MODEL_GPT4_0314:
        max_tokens = 8000
    elif model == const.MODEL_GPT4_32K:
        max_tokens = 32000
    elif model == const.MODEL_GPT_35_turbo_16K:
        max_tokens = 16000
    else:
        max_tokens = 4000
    return max_tokens

