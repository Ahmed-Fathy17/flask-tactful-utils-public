from abc import ABC, abstractmethod

class AbstractCacheStore(ABC):
    
    @abstractmethod
    def set(self, key, value, expires=None):
        pass

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def delete(self, key):
        pass
