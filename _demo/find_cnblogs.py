# -*- coding = utf-8 -*-
# @Time : 2022/4/27 8:21
# @Author :王敬博
# @File : test.py
# @Software: PyCharm
from bs4 import BeautifulSoup  #网页解析
import re    #正则表表达式文字匹配
import urllib.request,urllib.error  #指定url，获取网页数据
import xlwt  #进行excel操作
import sqlite3  #进行SQLite数据库操作
import pymysql.cursors  #连接mysql数据库

def main():
    baseurl = "https://www.cnblogs.com/wjingbo/default.html?page="
    datalist = getData(baseurl)         #调研分析数据函数
    #1 爬取网页
    savepath = ".\\权。的博客信息.xls"     #excel保存的位置名称
    saveData(datalist,savepath)          #调用保存函数



def askURL(url):
    head = {   #伪装请求头，模拟浏览器访问
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    request = urllib.request.Request(url,headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf-8')
        #print(html)
    except urllib.error.URLError as e:
        if hasattr(e,"code"):
            print(e.code)
        if hasattr(e,"reason"):
            print(e.reason)
    return html  #返回爬到所有的html数据

#正则表达式控制获取详细内容
findTitle = re.compile(r'<span>(.*?)</span>',re.S)
findlink = re.compile(r'<a class="postTitle2 vertical-middle" href="(.*?)">')
findzhaiyao = re.compile(r'<div class="c_b_p_desc"(.*?)<a',re.S)
finddate = re.compile(r'<div class="postDesc">posted @(.*?)权',re.S)
findread = re.compile(r'<span class="post-view-count" data-post-id=(.*?)</span>')
findcomment = re.compile(r'<span class="post-comment-count" data-post-id=(.*?)</span>')
finddigg = re.compile(r'<span class="post-digg-count" data-post-id=(.*?)</span>')

def getData(baseurl):
    datalist = []  # 2 解析数据
    allTitle = []  #存储标题
    allLink = []   #存储链接
    allZhaiyao = [] #存储摘要
    alldate = []    #存储日期
    allRead = []    #存储阅读数
    allComment = [] #存储评论数
    allDigg = []    #存储推荐数
    for i in range(0,10):
        url = baseurl + str(i+1)    #对目标链接地址page=后面的数字进行循环
        html = askURL(url)          #调用爬取的函数
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.find_all('div',class_="day"):  #简单过滤信息
            #print(item)

            item = str(item)

            title = re.findall(findTitle,item)     #匹配数据
            allTitle.extend(title)      #添加数据到列表

            link = re.findall(findlink,item)
            allLink.extend(link)

            zhaiyao = re.findall(findzhaiyao,item)
            allZhaiyao.extend(zhaiyao)

            date = re.findall(finddate,item)
            alldate.extend(date)

            readNum = re.findall(findread,item)
            allRead.extend(readNum)

            commentNum = re.findall(findcomment,item)
            allComment.extend(commentNum)

            diggNum = re.findall(finddigg,item)
            allDigg.extend(diggNum)
    #print(allTitle)
    #print(allLink)
    #print(allZhaiyao)
    #print(alldate)
    #print(allRead)
    #print(allComment)
    #print(allDigg)

    for j in range(0,100):      #循环10页就是100条数据，这个循环是过滤掉所有不需要的信息
        data = []
        title = allTitle[j].strip()     #去除字符串里的空格
        data.append(title)

        link = allLink[j]
        data.append(link)

        zhaiyao = allZhaiyao[j].strip()
        zhaiyao = zhaiyao.split('">')[1]
        data.append(zhaiyao.replace("\n",""))

        date = alldate[j].strip()
        data.append(date)

        readNum = allRead[j].split('>')[1]      #通过分割字符串来去除无用信息
        data.append(readNum)

        commentNum = allComment[j].split('>')[1]
        data.append(commentNum)

        diggNum = allDigg[j].split('>')[1]
        data.append(diggNum)

        datalist.append(data)

    print(datalist)
    return datalist     #返回列表

def saveData(datalist,savepath):
    print("save...")
    book = xlwt.Workbook(encoding="utf-8",style_compression=0)
    sheet = book.add_sheet('博客园随笔列表',cell_overwrite_ok=True)    #创建sheet1
    col = ("标题","原文链接","摘要","时间","阅读","评论","推荐")        #加标题
    for i in range(0,7):
        sheet.write(0,i,col[i])
    for i in range(0,100):          #添加数据到excel*（100条）
        print("第%d条"%(i+1))        #打印条数
        data = datalist[i]
        for j in range(0,7):
            sheet.write(i+1,j,data[j])      #添加每个子列表中的7个数据
    book.save(savepath)            #保存excel

if __name__ == "__main__":
    main()
    print("爬取完毕！")



