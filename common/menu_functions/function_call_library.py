import requests

from common import log
from config import conf

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
    },
}, ]


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
