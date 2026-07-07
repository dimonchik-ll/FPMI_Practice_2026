from __future__ import annotations

from shared.contracts import PlayerState, TOWER_DEFINITIONS, TowerKind


class Economy:
    def __init__(self, state: PlayerState | None = None) -> None:
        self.state = state or PlayerState()

    def select_tower(self, tower_kind: TowerKind) -> None:
        self.state.selected_tower = tower_kind

    def can_afford(self, amount: int) -> bool:
        return amount >= 0 and self.state.money >= amount

    def spend(self, amount: int) -> bool:
        if not self.can_afford(amount):
            return False
        self.state.money -= amount
        return True

    def can_buy(self, tower_kind: TowerKind) -> bool:
        return self.can_afford(TOWER_DEFINITIONS[tower_kind].cost)

    def buy(self, tower_kind: TowerKind) -> bool:
        return self.spend(TOWER_DEFINITIONS[tower_kind].cost)

    def add_reward(self, amount: int) -> None:
        self.state.money += amount
        self.state.score += amount

    def take_base_damage(self, amount: int) -> None:
        self.state.lives = max(0, self.state.lives - amount)

    def is_game_over(self) -> bool:
        return self.state.lives <= 0
