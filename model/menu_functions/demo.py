from model.menu_function import MenuFunction


class DemoFunction(MenuFunction):

    def getName(self) -> str:
        return "今日运势"

    def getDescription(self) -> str:
        return "#今日运势  <生日>"

    def getCmd(self) -> str:
        return "#今日运势"

    def execute(self, arg):
        return '吉吉'

    def getOrder(self) -> int:
        return 6
