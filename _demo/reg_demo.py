import os

import urllib

if __name__ == '__main__':

    url = "https://www.cnblogs.com/wuxinqiu/"
    str = "a123b"



    urlparse = urllib.parse.urlparse(url)

    print(urlparse.path)
    print(urlparse.path.replace("/", ""))

    print(urlparse.path[urlparse.path.rfind("/"):])

    file_path = "./tmp/cnblogs/3959524.html.txt"

    pathExists = os.path.exists(file_path)

    if not pathExists:
        with open(file_path, 'w', encoding='utf-8') as file_object:
            file_object.write(url)



    print(urlparse)

