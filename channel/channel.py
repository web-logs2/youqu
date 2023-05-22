"""
Message sending channel abstract class
"""

from bridge.bridge import Bridge
from model.menu_functions.menu_function import MenuFunction


class Channel(object):
    menuList: list[MenuFunction]
    menuString = '菜单列表 \n\n  ```java\n'
    menuDict: dict[str, MenuFunction] = {}

    def __init__(self):
        self.menuList: list[MenuFunction] = Bridge.fetch_menu_list(self)
        # self.menuList.append(DcoumentList())
        # self.menuList.append(DemoFunction())
        meuns = sorted(self.menuList, key=lambda x: x.getOrder())
        for item in meuns:
            self.menuDict[item.getCmd()] = item
            self.menuString += item.getCmd() + "        示例  " + item.getDescription() + "\n\n"

    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    def send(self, msg, receiver):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return: 
        """
        raise NotImplementedError

    def build_text_reply_content(self, query, context=None):
        if (query == '#菜单'):
            return self.menuString
        if (query.startswith("#")):
            cmds = query.split()
            cmd = self.menuDict.get(cmds[0])
            if cmd != None:
                return cmd.execute(cmds)
        return Bridge().fetch_text_reply_content(query, context)

    def build_picture_reply_content(self, query, context=None):
        return Bridge().fetch_picture_reply_content(query)

    def getMenuList(self) -> list[MenuFunction]:
        return Bridge.fetch_menu_list(self)

    async def build_reply_stream(self, query, context=None):
        if (query == '#菜单'):
            yield True, self.menuString
            return
        if query.startswith("#") and query != "#清除记忆":
            cmds = query.split()
            cmd = self.menuDict.get(cmds[0])
            if cmd is not None:
                res = cmd.execute(cmds)
                if type(res) == str:
                    yield True, res
                    return
                else:
                    response = ""
                    for token in res:
                        response += token
                        yield False, response
                    #yield True, response
                    #return
        else:
            async for final, response in Bridge().fetch_reply_stream(query, context):
                yield final, response
