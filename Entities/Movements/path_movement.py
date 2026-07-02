from Entities.Movements.movement_base import MovementBase
from Entities.entity_base import EntityBase
from Navigation.path import Path

class PathMovement(MovementBase):

    def __init__(self, path: Path) -> None:
        self._path = path
        self._current_waypoint = 0

    def update(self, entity: EntityBase, delta_time: float) -> None:
        if self._current_waypoint >= len(self._path):
            return

        target = self._path[self._current_waypoint]

        direction = target - entity.position
        distance = direction.length()

        if distance < 1:
            self._current_waypoint += 1
            return

        direction.normalize_ip()

        entity.position += direction * entity.speed * delta_time