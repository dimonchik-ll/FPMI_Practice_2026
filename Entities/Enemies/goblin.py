from Entities.Enemies.enemy_base import EnemyBase
from Entities.Movements.path_movement import PathMovement
from Navigation.path import Path
from pygame import Vector2, draw, Surface

class Goblin(EnemyBase):
    def __init__(self, position: Vector2, movement) -> None:
        super().__init__(
            position=position,
            speed=90,
            health=50,
            movement=movement
        )

    def draw(self, scene : Surface) -> None:
        draw.circle(
            scene,
            (255, 0, 0),
            (int(self.position.x), int(self.position.y)),
            6
        )

