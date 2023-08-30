import http.client
import json
import time

from common.log import logger
from config import project_conf

import hashlib
import urllib.parse


def get_payment_qr(transaction_id, total_fee, body, attach, time_expire='10m'):
    host = project_conf("payment_gateway")

    conn = http.client.HTTPSConnection(host)

    mch_id = project_conf("payment_gateway_mch_id")
    notify_url = project_conf("payment_gateway_notify_url")
    timestamp = str(int(time.time()))
    payload = "mch_id=" + mch_id + "&out_trade_no=" + transaction_id + "&total_fee=" + str(
        total_fee) + "&body=" + body + "&timestamp=" + timestamp + "&notify_url=" + notify_url + "&attach=" + attach + "&time_expire=" + time_expire
    # generate dict for sign
    request_dict = {
        "mch_id": mch_id,
        "out_trade_no": transaction_id,
        "total_fee": str(total_fee),
        "body": body,
        "timestamp": timestamp,
        "notify_url": notify_url,
    }
    sign_str = sign_lantu_payment(request_dict)
    payload += "&sign=" + sign_str
    logger.info("payload:{}".format(payload))

    headers = {'content-type': "application/x-www-form-urlencoded; charset=UTF-8"}

    conn.request("POST", "/api/wxpay/native", payload.encode('utf-8'), headers)

    res = conn.getresponse()
    data = json.loads(res.read())
    if data['code'] != 0:
        logger.error("transaction_id {} qr failed with error message:{}".format(transaction_id, data['msg']))
        # return data['msg']
        return None
    logger.info("request id:{}".format(data['request_id']))
    logger.info("url:{}".format(data['data']['QRcode_url']))
    return data['data']['QRcode_url']


def sign_lantu_payment(data: dict):
    key = project_conf("payment_gateway_mch_key")
    sorted_data = sorted(data.items(), key=lambda x: x[0])
    query_string = urllib.parse.urlencode(sorted_data)
    unquoted_query_string = urllib.parse.unquote(query_string)
    unquoted_query_string += "&key=" + key
    logger.debug("unquoted_query_string:{}".format(unquoted_query_string))
    sign = hashlib.md5(unquoted_query_string.encode()).hexdigest().upper()
    logger.info("sign:{}".format(sign))
    return sign


if __name__ == '__main__':
    # load config
    from config import load_config

    load_config()
    get_payment_qr("2sdfd233211", 1, "test", "test", "2021-01-01 00:00:00",
                   "wx9a7e8f8e2b7e9a5a")
