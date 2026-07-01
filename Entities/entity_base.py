import abc
from constants import *

class EntityBase(abc.ABC):
    @abc.abstractmethod 
    def draw(self): pass
    @abc.abstractmethod 
    def update(self): pass
