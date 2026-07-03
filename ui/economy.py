from __future__ import annotations

from shared.contracts import PlayerState, TOWER_DEFINITIONS, TowerKind


class Economy:
    def __init__(self, state: PlayerState | None = None) -> None:
        self.state = state or PlayerState()

    def select_tower(self, tower_kind: TowerKind) -> None:
        self.state.selected_tower = tower_kind

    def can_buy(self, tower_kind: TowerKind) -> bool:
        return self.state.money >= TOWER_DEFINITIONS[tower_kind].cost

    def buy(self, tower_kind: TowerKind) -> bool:
        definition = TOWER_DEFINITIONS[tower_kind]
        if self.state.money < definition.cost:
            return False
        self.state.money -= definition.cost
        return True

    def add_reward(self, amount: int) -> None:
        self.state.money += amount
        self.state.score += amount

    def take_base_damage(self, amount: int) -> None:
        self.state.lives = max(0, self.state.lives - amount)

    def is_game_over(self) -> bool:
        return self.state.lives <= 0
