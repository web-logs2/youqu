import datetime
import os
import urllib

import requests
from bs4 import BeautifulSoup
from llama_index import SimpleDirectoryReader

from common import const
from common import log
from common.db.document_record import DocumentRecord
from config import model_conf
from model.menu_functions.menu_function import MenuFunction
from model.menu_functions.public_train_methods import public_train_documents

os.environ["OPENAI_API_KEY"] = model_conf(const.OPEN_AI).get('api_key')


class CnblogsPreTrainDocument(MenuFunction):

    def getName(self) -> str:
        return "训练博客园"

    def getDescription(self) -> str:
        return "#训练博客园  <url>"

    def getCmd(self) -> str:
        return "#训练博客园"

    def execute(self, arg) -> any:
        if (len(arg) <= 1):
            return "请输入博客园地址或博主的简称(url地址上的名字)"
        try:
            url = arg[1]

            # #训练博客园 https://www.cnblogs.com/wuxinqiu/
            # #训练博客园 wuxinqiu

            if url.startswith("http"):
                urlparse = urllib.parse.urlparse(url)
                authorName = urlparse.path.replace("/", "")
            else:
                authorName = url

            index_path = './tmp/cnblogs/' + authorName + '/index.json'

            changed = self.init_cnblogs(authorName, index_path)

            if changed:
                documents = SimpleDirectoryReader('./tmp/cnblogs/' + authorName + '/').load_data()
                # index = GPTSimpleVectorIndex.from_documents(documents)
                index = public_train_documents(documents)
                # index.save_to_disk(index_path)
                index.storage_context.persist(persist_dir=index_path)

            return '训练完成'
        except Exception as e:
            log.exception(e)
            return '训练失败，请重试'

    def getOrder(self) -> int:
        return 5

    def init_cnblogs(self, arg, index_path) -> any:
        # 标记有没有新增博客
        changed = False
        url = "https://www.cnblogs.com/" + arg + "/"
        author = DocumentRecord.select().where((DocumentRecord.title == arg) & (DocumentRecord.type == "cnblogs"))
        if (author.count() <= 0):
            new_author = DocumentRecord(
                user_id=0,
                title=arg,
                path=url,
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now(),
                trained=True,
                trained_file_path=index_path,
                type='cnblogs'
            )
            new_author.save()

        # 创建文件夹，存放博客内容
        tmpFilePath = './tmp/cnblogs/' + arg + '/'
        pathExists = os.path.exists(tmpFilePath)
        if not pathExists:
            os.makedirs(tmpFilePath)

        # 从第一页开始抓，到第N页，如果没有数据就停止
        page = 1
        while True:
            request_url = url
            if page > 1:
                request_url = url + "?page=" + str(page)
            html = self.get_cnblogs_html(request_url)
            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a", class_="postTitle2")
            #
            if (len(links) == 0):
                break
            for link in links:
                href = link.get("href")

                # 将href最后的一截当做文件名字
                urlparse = urllib.parse.urlparse(href)
                file_path = tmpFilePath + urlparse.path[urlparse.path.rfind("/") + 1:] + ".txt"

                filePathExists = os.path.exists(file_path)
                if filePathExists:
                    continue

                # 有新博客
                changed = True

                content = self.get_cnblogs_html(href)
                text = self.get_cnblogs_content(content)
                with open(file_path, 'w', encoding='utf-8') as file_object:
                    file_object.write(text)
            page = page + 1
        return changed

    def get_cnblogs_content(self, content) -> any:
        soup = BeautifulSoup(content, "html.parser")
        cnblogs_post_body = soup.find("div", id="cnblogs_post_body")
        return cnblogs_post_body.get_text()

    def get_cnblogs_html(self, arg) -> any:
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30"
        }
        r = requests.post(arg, headers=headers)
        return r.text
