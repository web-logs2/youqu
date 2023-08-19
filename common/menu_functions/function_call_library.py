import logging
from datetime import datetime

import pytz
import requests
from flask import request

from common import log
from config import conf
from service.tencent_stock import get_cn_quotes, get_us_quotes

functions_definition = [{
    "name": "send_mail",
    "description": "Send mail to user and return the result",
    "parameters": {
        "type": "object",
        "required": ["mail", "msg"],
        "properties": {
            "mail": {
                "type": "string",
                "description": "A email address",
            },
            "msg": {
                "type": "string",
                "description": "The content of the mail"
            },
        },
    },
}, {
    "name": "get_weather_by_location",
    "description": "",
    "parameters": {
        "type": "object",
        "required": ["city", "units"],
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, state code and country code divided by comma in English, "
                               "use ISO 3166 country codes.",
            },
            "units": {
                "type": "string",
                "description": "available in Fahrenheit, Celsius and Kelvin units. "
                               "For temperature in Fahrenheit use units=imperial, "
                               "for Celsius use units=metric and Kelvin units by default"
            },
        }
    }
},
    {
        "name": "get_us_stock_price",
        "description": "get us stock price",
        "parameters": {
            "type": "object",
            "required": ["code", "date"],
            "properties": {
                "code": {
                    "type": "string",
                    "description": "code of a US stock, e.g. AAPL",
                },
                "date": {
                    "type": "string",
                    "description": "optional, date of the stock price, e.g. 2021-05-28"
                },
            }
        }
    },
    {
        "name": "get_cn_stock_price",
        "description": "get China mainland stock price",
        "parameters": {
            "type": "object",
            "required": ["code", "date"],
            "properties": {
                "code": {
                    "type": "string",
                    "description": "code of a china stock, e.g. sh600036 or sz000001",
                },
                "date": {
                    "type": "string",
                    "description": "optional, date of the stock price, e.g. 2021-05-28 "
                },
            }
        }
    },
    {
        "name": "get_current_time_and_timezone",
        "description": "get current time and timezone",
        "parameters": {
            "type": "object",
            "required": [],
            "properties": {
            }
        }
    },
]


def detect_function_and_call(function_name, parameters):
    for function in functions_definition:
        if function.get("name") == function_name:
            return eval(function_name)(**parameters)
    log.error("Function {} not found!".format(function_name))
    return "Function {} not found!".format(function_name)


def send_mail(mail, msg):
    log.info("send mail triggered, send: {} to {}".format(msg, mail))
    return "mail sent!"


# https://openweathermap.org/current
# parameter log:
# {
#   q: {
#       {city name}
#       {city name},{country code}
#       {city name},{state code},{country code}
#
#       City name, state code and country code divided by comma, use ISO 3166 country codes.
#
#       You can specify the parameter not only in English.
#       In this case, the API response should be returned in the same language as the language of
#       requested location name if the location is in our predefined list of more than 200,000 locations.
#   },
#   lang: {
#       af->Afrikaans, al->Albanian, ar->Arabic, az->Azerbaijani, bg->Bulgarian, ca->Catalan, cz->Czech,
#       da->Danish, de->German, el->Greek, en->English, eu->Basque, fa->Persian (Farsi), fi->Finnish,
#       fr->French, gl->Galician, he->Hebrew, hi->Hindi, hr->Croatian, hu->Hungarian, id->Indonesian,
#       it->Italian, ja->Japanese, kr->Korean, la->Latvian, lt->Lithuanian, mk->Macedonian, no->Norwegian,
#       nl->Dutch, pl->Polish, pt->Portuguese, pt_br->Português Brasil, ro->Romanian, ru->Russian,
#       sv/se->Swedish, sk->Slovak, sl->Slovenian, sp/es->Spanish, sr->Serbian, th->Thai, tr->Turkish,
#       ua/uk->Ukrainian, vi->Vietnamese, zh_cn->Chinese Simplified, zh_tw->Chinese Traditional, zu->Zulu
#   },
#   units: {
#       standard, default value, Temperature in Kelvin, no need to use units parameter in API call
#       metric, For temperature in Celsius use units=metric
#       imperial, For temperature in Fahrenheit use units=imperial
#   },
# }
#
# 可以根据IP查询地址, 再根据地址查询天气
def get_weather_by_location(city, units="standard", latitude=None, longitude=None):
    api_key = conf().get("functions_library").get("openWeather_api_key")

    response = requests.get(url="https://api.openweathermap.org/data/2.5/weather?"
                                "appid={}&q={}&units={}&lang={}"
                            .format(api_key, city, units, "zh_cn"))

    return response.text


# def get_latest_chinese_stock_price(self, stock_name, stock_code):
#     requests.post(url="http://stock.salefx.cn:10000/api/stock/realTime", json={"code": stock_code})


def get_us_stock_price(code, date=None):
    code = code.upper()
    if date is None:
        # 如果没有提供日期，默认为当天
        result = get_us_quotes(code)
    else:
        # 如果提供了日期，获取该日期的收盘价
        return "Specific date query is not implemented yet!"
    if result is not None:
        log.info("result:{}", result)
        return str(result[0].get("price"))


def get_cn_stock_price(code, date=None):
    code = code.lower()
    if date is None:
        # 如果没有提供日期，默认为当天
        result = get_cn_quotes(code)
    else:
        # 如果提供了日期，获取该日期的收盘价
        return "Specific date query is not implemented yet!"
    if result is not None:
        # log.info("result:{}",result)
        return str(result[0].get("price"))


def get_current_time_and_timezone():
    try:
        # get public ip
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        # get location info by ip
        data = requests.get(f'https://ipapi.co/{ip}/json/').json()

        # get timezone by location
        location_tz = data['timezone']

        tz = pytz.timezone(location_tz)
    except:
        # if fail, use Beijing timezone
        location_tz = 'Asia/Shanghai'
        tz = pytz.timezone(location_tz)

    now = datetime.now(tz)

    return now.strftime("%Y-%m-%d %H:%M:%S") + f', Timezone: {location_tz}'
