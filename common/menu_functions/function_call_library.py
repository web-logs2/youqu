import logging
from datetime import datetime

import pytz
import requests
from flask import request

from common import log
from common.log import logger
from config import conf
from service.google_search import search_google
from service.tencent_stock import get_cn_quotes, get_us_quotes



def detect_function_and_call(function_name, parameters,functions_definition):
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


def query_cheap_flight(from_city, to_city, start_date, end_date, max_price, direct="false"):
    ##convert max_price to int
    max_price = int(max_price)

    # use this api
    # https://flights.ctrip.com/itinerary/api/12808/lowestPrice?

    # flightWay=Oneway >Oneway单向飞 Roundtrip往返
    #
    # dcity=NNG >出发地（编号对应的地点看下面的tx），这里是南宁
    #
    # acity=WUH >目的地（编号对应的地点看下面的tx），这里是武汉
    #
    # direct=true >是否直飞(不转站)true:是，false:否
    #
    # army=false >可加可不加

    # return "the cheapest flight from {} to {} from {} to {} with max price{} and direct flight{}".format(from_city, to_city, start_date, end_date, max_price, direct)
    url = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
    #
    url += "flightWay=Oneway"
    url += "&dcity=" + from_city
    url += "&acity=" + to_city
    url += "&direct=" + direct
    logger.info(url)
    try:
        data = requests.get(url).json()
        if data == None:
            logger.info('请求携程机票接口错误：' + url)
            return '请求携程机票接口错误：'
        cheap_prices = data['data']['oneWayPrice'][0]
        valid_prices = {date: price for date, price in cheap_prices.items()
                        if start_date <= date <= end_date and price <= max_price}
        sorted_prices = dict(sorted(valid_prices.items(), key=lambda item: item[1]))
        logger.info(sorted_prices)
        return str(sorted_prices)

    except Exception as ex:
        logger.info(ex)
        return '请求携程机票接口错误：'


def search_google_get_contents(key):
    return search_google(key)
