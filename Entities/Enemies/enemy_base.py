from abc import ABC
from Entities.Movements.movement_base import MovementBase
from Entities.entity_base import EntityBase
from pygame import Vector2

class EnemyBase(EntityBase, ABC):

    def __init__(self,
                 position: Vector2,
                 speed:float,
                 health: int,
                 movement : MovementBase) -> None:
        super().__init__(position, speed)
        self._health = health
        self._movement = movement

    def update(self, delta_time : float) -> None:
        self._movement.update(self, delta_time)

