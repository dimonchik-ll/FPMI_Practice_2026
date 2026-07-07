from __future__ import annotations

import pygame
import pytest

from shared.contracts import (
    GameSnapshot,
    PlayerState,
    TowerKind,
    TowerView,
    UiActionKind,
    Vector2,
)
from ui.layout import UiLayout
from ui.theme import UiFonts, UiTheme
from ui.tower_action_menu import TowerActionMenu


@pytest.fixture(autouse=True)
def initialized_pygame():
    if not pygame.get_init():
        pygame.init()
    yield


def snapshot(*, money: int = 200, tower: TowerView | None = None) -> GameSnapshot:
    player = PlayerState(money=money).to_view()
    return GameSnapshot(
        player=player,
        wave_number=1,
        enemies=(),
        towers=() if tower is None else (tower,),
        wave_is_active=False,
        game_over=False,
        victory=False,
    )


def tower_view(
    *,
    kind: TowerKind = TowerKind.ARCHER_1,
    level: int = 1,
    upgrade_cost: int | None = 70,
) -> TowerView:
    return TowerView(
        identifier="tower-1",
        kind=kind,
        position=Vector2(100.0, 100.0),
        cell=(1, 1),
        cooldown_remaining=0.0,
        level=level,
        damage=12,
        attack_range=135.0,
        attacks_per_second=1.1,
        attack_type="single",
        upgrade_cost=upgrade_cost,
    )


def menu() -> TowerActionMenu:
    return TowerActionMenu(UiLayout(640, 480), UiTheme(), UiFonts())


def click(rect: pygame.Rect) -> pygame.event.Event:
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": rect.center},
    )


def test_upgrade_button_returns_upgrade_action_for_affordable_tower() -> None:
    action_menu = menu()
    action_menu.open("tower-1")
    state = snapshot(tower=tower_view())

    action = action_menu.handle_event(click(action_menu._upgrade_button_rect()), state)

    assert action is not None
    assert action.kind == UiActionKind.UPGRADE_TOWER
    assert action.payload == {"tower_id": "tower-1"}


def test_upgrade_button_is_inactive_when_money_is_insufficient() -> None:
    action_menu = menu()
    action_menu.open("tower-1")
    state = snapshot(money=30, tower=tower_view())

    action = action_menu.handle_event(click(action_menu._upgrade_button_rect()), state)

    assert action is None


def test_delete_button_returns_remove_action() -> None:
    action_menu = menu()
    action_menu.open("tower-1")
    state = snapshot(tower=tower_view())

    action = action_menu.handle_event(click(action_menu._delete_button_rect()), state)

    assert action is not None
    assert action.kind == UiActionKind.REMOVE_TOWER
    assert action.payload == {"tower_id": "tower-1"}


def test_menu_closes_when_selected_tower_disappears() -> None:
    action_menu = menu()
    action_menu.open("tower-1")

    action_menu.sync(snapshot())

    assert not action_menu.is_open
