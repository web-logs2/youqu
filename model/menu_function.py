from abc import abstractmethod


class MenuFunction:
    @abstractmethod
    def getName(self) -> str:
        pass
    
    @abstractmethod
    def getDescription(self)-> str:
        pass
    
    @abstractmethod
    def getCmd(self)-> str:
        pass
    
    @abstractmethod
    def excetu(self, arg)-> any:
        pass
    
    @abstractmethod
    def getOrder(self)-> int:
        pass