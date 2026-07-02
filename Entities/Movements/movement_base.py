from abc import ABC, abstractmethod
from Entities.entity_base import EntityBase

class MovementBase(ABC):

    @abstractmethod
    def update(self, entity : EntityBase, delta_time : float) -> None:
        pass
