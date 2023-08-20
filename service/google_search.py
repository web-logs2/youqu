from bs4 import BeautifulSoup

from common.functions import num_tokens_from_string
from common.log import logger
from googlesearch import search
import requests


def get_content_by_url(url):
    try:
        response = requests.get(url)  # 获取网页内容，返回的是HTML代码
        page_content = response.text  # 使用BeautifulSoup解析这段代码
        soup = BeautifulSoup(page_content, 'html.parser')  # 现在你可以通过soup对象获取你需要的任意网页元素，
        # 例如获取所有的段落<p>标签：
        paragraphs = soup.find_all('p')  # 打印出第一个段落的文字
        # print(paragraphs[0].get_text())
        # return all paragraphs text
        return '\n'.join([paragraph.get_text() for paragraph in paragraphs])
    except Exception as e:
        return ""


def search_google(key):
    result = ""
    for url in search(key,num_results=10):
        logger.info("current url:"+url)
        result = result + get_content_by_url(url)
        if num_tokens_from_string(result) > 10000:
            logger.info("Too many results, break")
            break
    logger.info(result)
    return result
