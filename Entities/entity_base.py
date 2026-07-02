from abc import ABC, abstractmethod
from pygame import Vector2, Surface

class EntityBase(ABC):

    def __init__(self, position: Vector2, speed: float) -> None:
        self.position = position
        self.speed = speed

    @abstractmethod
    def draw(self, scene : Surface) -> None:
        pass

    @abstractmethod
    def update(self, delta_time : float) -> None:
        pass
