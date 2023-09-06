import datetime
import os
import time

import numpy as np
import requests
from bs4 import BeautifulSoup
from llama_index import SimpleDirectoryReader

from common import const
from common import log
from common.db.document_record import DocumentRecord
from common.menu_functions.menu_function import MenuFunction
from common.menu_functions.public_train_methods import public_train_documents
from config import model_conf

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class WxPreTrainDocument(MenuFunction):

    def getName(self) -> str:
        return "训练微信公众号"

    def getDescription(self) -> str:
        return "#训练微信公众号  <name> <option>"

    def getCmd(self) -> str:
        return "#训练微信公众号"

    def execute(self, arg) -> any:
        if (len(arg) <= 1):
            return "请输入输入微信公众号的名字"
        try:
            authorName = arg[1]

            # 只抓取部分文章
            count = 0
            if len(arg) == 3:
                count = int(arg[2])

            # 每个公众号都有一个唯一ID，字节调动技术团队（MzI1MzYzMjE0MQ==）
            # #训练微信公众号 字节跳动技术团队
            # #训练微信公众号 字节跳动技术团队 50

            fakeid = self.get_fakeid(authorName)
            index_path = './tmp/wx/' + authorName + '/index.json'
            success = self.init_appmsg(authorName, fakeid, index_path, count)
            if success:
                documents = SimpleDirectoryReader('./tmp/wx/' + fakeid + '/').load_data()
                # index = GPTSimpleVectorIndex.from_documents(documents)
                index = public_train_documents(documents)
                index.storage_context.persist(persist_dir=index_path)
                # index.save_to_disk(index_path)

            return '训练完成'
        except Exception as e:
            log.exception(e)
            return '训练失败，请重试' + str(e)

    def getOrder(self) -> int:
        return 7

    def get_fakeid(self, authorName) -> any:
        author = DocumentRecord.select().where((DocumentRecord.title == authorName) & (DocumentRecord.type == "wx"))
        if (author.count() > 0):
            return author[0].path

        url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        headers = {
            "Cookie": "appmsglist_action_3862945393=card; rewardsn=; wxtokenkey=777; wwapp.vid=; wwapp.cst=; wwapp.deviceid=; ua_id=taggKKdL9tcIIs26AAAAAF5RrcS4yM6PfojApzMf-p0=; wxuin=80343254898701; cert=o1uz17vucOezFYCR4aqduzY9CrbabOb6; mm_lang=zh_CN; use_waban_ticket=1; media_ticket=85499ac075c1bbe29ad040740f360d221c76bef6; media_ticket_id=gh_3cd078544ed6; pgv_info=ssid=s4612374648; pgv_pvid=639369940; xid=18851611e4a54718c3ce4c9a2c27064b; uuid=3de5b1834464006a37bbe6123627ac7f; sig=h01e55e99d277467842461a38c257c0ee8d63ee085c9c084594e430fda2ac7d1a8c3066bcb378eaf959; data_bizuin=3862945393; bizuin=3862945393; master_user=gh_1192ba6442d3; master_sid=ZFRIcm8yN3NHaEFHOTVYbEdHYWxXd3hydVJNYUhvOFBVX2RwMG85WGlLdkEzUzBMV0pyNXRhVmdOeU1tb3dSdU1GanFQQm12elpqV1JqWTQ0bUROY3JlQW9Oakl2YW1iU1pRemF2RHBxY1pmR1FTc0JsajFqVnRxcTZnSzNaR1B2Wnc4T20zVDRLN1AzVldX; master_ticket=fe557b1d7b2a176ef30529a83c1f6bc6; data_ticket=KV1iqjmEXPB6KkDKVz/U1ENVAbuIb+jtHsYy7CQCRtmMag1GQ7WehS/hZFM3mPxe; rand_info=CAESIL1Jjhd67iWhdrdwVGV4GWN5/t39bryDMhgPtamZ4Vag; slave_bizuin=3862945393; slave_user=gh_1192ba6442d3; slave_sid=NkNqckhWYUNBN1Z0R1cyQ0RnRGduVDc3bklhSjhYM0FLWmlRNkRieDZtWUpVdktURlUxb2lMUzJvN3paSGNnZmppekdUTHJSaV93MXJuZmtVcmI2RE03MUpXNWE5c25kWHN1MmIzakRTUm5KSG02ZUJWNG5WY0VWQm01QWo3VFIyWExNajk5ZmFwSThCU3Nm; _clck=3862945393|1|fah|0; _clsk=1fixa1c|1680573869901|3|1|mp.weixin.qq.com/weheat-agent/payload/record",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        }
        data = {
            "action": "search_biz",
            "begin": 0,  # 第几页
            "count": 5,  # 每页几条
            "query": authorName,
            "token": "797790692",  # 需要定期修改
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }
        # 随机等待几秒，避免被微信识别到
        time.sleep(np.random.randint(3, 15))
        proxies = {'http': '116.6.232.251'}
        content_json = requests.get(url, headers=headers, params=data, proxies=proxies, verify=False).json()
        if content_json["total"] > 1:
            for item in content_json["list"]:  # 提取信息
                if authorName == item["nickname"]:
                    fakeid = item["fakeid"]
                    return fakeid
            raise Exception("公众号名字不唯一，请输入唯一的名字")
        return content_json["list"][0].fakeid

    def get_headers(self) -> any:
        # 使用Cookie，跳过登陆操作
        # headers 根据自己电脑修改
        headers = {
            "Cookie": "appmsglist_action_3862945393=card; rewardsn=; wxtokenkey=777; wwapp.vid=; wwapp.cst=; wwapp.deviceid=; ua_id=taggKKdL9tcIIs26AAAAAF5RrcS4yM6PfojApzMf-p0=; wxuin=80343254898701; cert=o1uz17vucOezFYCR4aqduzY9CrbabOb6; mm_lang=zh_CN; use_waban_ticket=1; media_ticket=85499ac075c1bbe29ad040740f360d221c76bef6; media_ticket_id=gh_3cd078544ed6; pgv_info=ssid=s4612374648; pgv_pvid=639369940; xid=18851611e4a54718c3ce4c9a2c27064b; uuid=3de5b1834464006a37bbe6123627ac7f; sig=h01e55e99d277467842461a38c257c0ee8d63ee085c9c084594e430fda2ac7d1a8c3066bcb378eaf959; data_bizuin=3862945393; bizuin=3862945393; master_user=gh_1192ba6442d3; master_sid=ZFRIcm8yN3NHaEFHOTVYbEdHYWxXd3hydVJNYUhvOFBVX2RwMG85WGlLdkEzUzBMV0pyNXRhVmdOeU1tb3dSdU1GanFQQm12elpqV1JqWTQ0bUROY3JlQW9Oakl2YW1iU1pRemF2RHBxY1pmR1FTc0JsajFqVnRxcTZnSzNaR1B2Wnc4T20zVDRLN1AzVldX; master_ticket=fe557b1d7b2a176ef30529a83c1f6bc6; data_ticket=KV1iqjmEXPB6KkDKVz/U1ENVAbuIb+jtHsYy7CQCRtmMag1GQ7WehS/hZFM3mPxe; rand_info=CAESIL1Jjhd67iWhdrdwVGV4GWN5/t39bryDMhgPtamZ4Vag; slave_bizuin=3862945393; slave_user=gh_1192ba6442d3; slave_sid=NkNqckhWYUNBN1Z0R1cyQ0RnRGduVDc3bklhSjhYM0FLWmlRNkRieDZtWUpVdktURlUxb2lMUzJvN3paSGNnZmppekdUTHJSaV93MXJuZmtVcmI2RE03MUpXNWE5c25kWHN1MmIzakRTUm5KSG02ZUJWNG5WY0VWQm01QWo3VFIyWExNajk5ZmFwSThCU3Nm; _clck=3862945393|1|fah|0; _clsk=1fixa1c|1680573869901|3|1|mp.weixin.qq.com/weheat-agent/payload/record",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        }
        return headers

    def init_appmsg(self, authorName, fakeid, index_path, count) -> any:
        url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        # 使用Cookie，跳过登陆操作
        # headers 根据自己电脑修改
        headers = self.get_headers()
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
        author = DocumentRecord.select().where((DocumentRecord.title == authorName) & (DocumentRecord.type == "wx"))
        if (author.count() <= 0):
            author = DocumentRecord(
                user_id=0,
                title=authorName,
                path=fakeid,
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now(),
                trained=False,
                trained_file_path=index_path,
                type='wx'
            )
            author.save()
            author_id = author.get_id()
        else:
            author_id = author[0].id

        # 创建文件夹，存放内容
        tmpFilePath = './tmp/wx/' + fakeid + '/'
        pathExists = os.path.exists(tmpFilePath)
        if not pathExists:
            os.makedirs(tmpFilePath)
        # 爬完所有文章标记成功，其它标记失败，并且标记训练未完成
        success = True
        # 从第一页开始抓，到第N页，如果没有数据就停止
        page = 1
        total = 0
        try:
            while True:
                data["begin"] = (page - 1) * 5
                # 随机等待几秒，避免被微信识别到
                time.sleep(np.random.randint(3, 10))
                content_json = requests.get(url, headers=headers, params=data, proxies=proxies, verify=False).json()
                # 抓取失败，退出
                if content_json['base_resp']['ret'] == 200013:
                    print("触发微信机制，抓取失败，当前抓取第{0}页，每页{1}篇".format((page + 1), 5))
                    success = False
                    break
                # 抓取完成，结束
                if len(content_json['app_msg_list']) == 0:
                    print("已抓取完所有文章，共抓取{0}篇".format((page + 1) * 5))
                    break
                # 返回了一个json，里面是每一页的数据
                for it in content_json["app_msg_list"]:  # 提取信息
                    aid = it["aid"]
                    link = it["link"]
                    # aid当做文件名字
                    file_path = tmpFilePath + aid + ".txt"

                    # 文件已存在
                    filePathExists = os.path.exists(file_path)
                    if filePathExists:
                        total = total + 1
                        continue

                    # 随机等待几秒，避免被微信识别到
                    time.sleep(np.random.randint(4, 15))
                    text = self.get_wx_body(link)
                    with open(file_path, 'w', encoding='utf-8') as file_object:
                        file_object.write(text)
                    total = total + 1
                page = page + 1
                if (count > 0) & (total > count):
                    break
        except Exception as e:
            log.exception(e)
            success = False
        # 标记失败
        if not success:
            DocumentRecord.update(trained=False).where(DocumentRecord.id == author_id).execute()
        else:
            DocumentRecord.update(trained=True).where(DocumentRecord.id == author_id).execute()
        return success

    def get_wx_body(self, arg) -> any:
        headers = self.get_headers()
        # 直接用这个连接暂时获取不到内容
        html = requests.get(arg, headers=headers)
        soup = BeautifulSoup(html.text, "lxml")
        wx_post_body = soup.find("div", id="js_content")
        return wx_post_body.get_text()
