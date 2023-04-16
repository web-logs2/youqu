import time

import numpy as np
import pandas as pd
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


def get_weixin(fakeid):
    url = "https://mp.weixin.qq.com/cgi-bin/appmsg"

    # 使用Cookie，跳过登陆操作
    # headers 根据自己电脑修改
    headers = {
        "Cookie": "appmsglist_action_3862945393=card; rewardsn=; wxtokenkey=777; wwapp.vid=; wwapp.cst=; wwapp.deviceid=; ua_id=taggKKdL9tcIIs26AAAAAF5RrcS4yM6PfojApzMf-p0=; wxuin=80343254898701; cert=o1uz17vucOezFYCR4aqduzY9CrbabOb6; mm_lang=zh_CN; use_waban_ticket=1; media_ticket=85499ac075c1bbe29ad040740f360d221c76bef6; media_ticket_id=gh_3cd078544ed6; pgv_info=ssid=s4612374648; pgv_pvid=639369940; xid=18851611e4a54718c3ce4c9a2c27064b; uuid=3de5b1834464006a37bbe6123627ac7f; sig=h01e55e99d277467842461a38c257c0ee8d63ee085c9c084594e430fda2ac7d1a8c3066bcb378eaf959; data_bizuin=3862945393; bizuin=3862945393; master_user=gh_1192ba6442d3; master_sid=ZFRIcm8yN3NHaEFHOTVYbEdHYWxXd3hydVJNYUhvOFBVX2RwMG85WGlLdkEzUzBMV0pyNXRhVmdOeU1tb3dSdU1GanFQQm12elpqV1JqWTQ0bUROY3JlQW9Oakl2YW1iU1pRemF2RHBxY1pmR1FTc0JsajFqVnRxcTZnSzNaR1B2Wnc4T20zVDRLN1AzVldX; master_ticket=fe557b1d7b2a176ef30529a83c1f6bc6; data_ticket=KV1iqjmEXPB6KkDKVz/U1ENVAbuIb+jtHsYy7CQCRtmMag1GQ7WehS/hZFM3mPxe; rand_info=CAESIL1Jjhd67iWhdrdwVGV4GWN5/t39bryDMhgPtamZ4Vag; slave_bizuin=3862945393; slave_user=gh_1192ba6442d3; slave_sid=NkNqckhWYUNBN1Z0R1cyQ0RnRGduVDc3bklhSjhYM0FLWmlRNkRieDZtWUpVdktURlUxb2lMUzJvN3paSGNnZmppekdUTHJSaV93MXJuZmtVcmI2RE03MUpXNWE5c25kWHN1MmIzakRTUm5KSG02ZUJWNG5WY0VWQm01QWo3VFIyWExNajk5ZmFwSThCU3Nm; _clck=3862945393|1|fah|0; _clsk=1fixa1c|1680573869901|3|1|mp.weixin.qq.com/weheat-agent/payload/record",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    }

    data = {
        "action": "list_ex",
        "begin": 0,  # 第几页
        "count": 5,  # 每页几条
        "fakeid": "MzI1MzYzMjE0MQ==",
        "type": "9",
        "query": "",
        "token": "797790692",  # 需要定期修改
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1"
    }

    proxies = {'http': '116.6.232.251'}
    title = []
    link = []
    time1 = []
    # 随机等待几秒，避免被微信识别到
    time.sleep(np.random.randint(3, 15))

    content_json = requests.get(url, headers=headers, params=data, proxies=proxies, verify=False).json()

    # 返回了一个json，里面是每一页的数据
    for it in content_json["app_msg_list"]:  # 提取信息
        title.append(it["title"])  # 标题
        link.append(it["link"])  # 链接
        time1.append(it['create_time'])  # 时间

        print(it["title"])

    columns = {'title': title, 'link': link, 'time': time1}  # 组成df文件
    df = pd.DataFrame(columns)
    return df


if __name__ == '__main__':
    get_weixin("MzU3ODkyNzI4OQ==")