import requests
from bs4 import BeautifulSoup
from googlesearch import search

from common.functions import num_tokens_from_string
from common.log import logger


def get_content_by_url(url):
    try:
        resp = requests.get(url)
        resp.encoding = resp.apparent_encoding  # 使用正确的编码
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 例如获取所有的段落<p>标签：
        paragraphs = soup.find_all('p')  # 打印出第一个段落的文字
        # print(paragraphs[0].get_text())
        # return all paragraphs text
        return '\n'.join([paragraph.get_text() for paragraph in paragraphs])
    except Exception as e:
        return ""


def search_google(key):
    result = ""
    current_size = 0
    for url in search(key, num_results=5):
        logger.info("current url:" + url)
        tem_result = get_content_by_url(url)
        logger.info("current result:" + tem_result)
        tem_result_size = num_tokens_from_string(tem_result)
        if current_size + tem_result_size > 8000:
            logger.info("Too many results, break")
            break
        else:
            result = f"{result}\n{tem_result}"
            current_size = current_size + num_tokens_from_string(tem_result)
    return result
