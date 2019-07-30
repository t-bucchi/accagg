from abc import ABCMeta, abstractmethod

class Scraper(metaclass = ABCMeta):
    @classmethod
    @abstractmethod
    def id(self):
        pass

    @abstractmethod
    def search(self, name):
        pass

    @abstractmethod
    def getinfo(self, id):
        pass

    @abstractmethod
    def price_log(self, id):
        pass
