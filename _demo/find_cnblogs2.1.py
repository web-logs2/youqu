# Author: Lovyya
# File : blog_spider
import json
import re

import requests
from bs4 import BeautifulSoup

# 这个是为和老师的urls一致性 匹配urls里面的数字
rule = re.compile("\d+")

urls = [f'https://www.cnblogs.com/#p{page}' for page in range(1, 31)]

# pos请求网址
url = "https://www.cnblogs.com/AggSite/AggSitePostList"
headers = {
    "content-type": "application/json",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30"
}

def craw(urls):
    #idx 是'xxx.xxxx.xxx/#p{num}' 里面的num 这样写可以不用改 后面生产者消费者的代码
    idx = rule.findall(urls)[0]
    # payload参数 只需要更改 idx 就行
    payload = {
        "CategoryType": "SiteHome",
        "ParentCategoryId": 0,
        "CategoryId": 808,
        "PageIndex": idx,
        "TotalPostCount": 4000,
        "ItemListActionName": "AggSitePostList"
    }
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return r.text

def parse(html):
    # post-item-title
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", class_="post-item-title")
    return [(link["href"], link.get_text()) for link in links]

if __name__ == '__main__':
    url = "https://www.cnblogs.com/burc/p/17254663.html"
    html = craw(url)
    soup = BeautifulSoup(html, "html.parser")
    cnblogs_post_body = soup.find("div", id="cnblogs_post_body")
    print(cnblogs_post_body.get_text())
