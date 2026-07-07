from __future__ import annotations

import sys
from types import SimpleNamespace

from shared.contracts import BuildRequest, TowerKind, Vector2
from shared.asset_manifest import ARROW_SHEET, TOWER_IDLE_ASSETS, TOWER_UNIT_SHEETS
from towers.models import Facing, Projectile, TargetPriority, TowerRuntime
from towers.sprites import TowerRenderer


class _Rect:
    def __init__(self, x=0, y=0, width=0, height=0, **kwargs) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = kwargs.get("center", (x + width // 2, y + height // 2))
        self.midbottom = kwargs.get("midbottom", (x + width // 2, y + height))

    def contains(self, other) -> bool:
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.x + self.width >= other.x + other.width
            and self.y + self.height >= other.y + other.height
        )

    def inflate(self, width, height):
        return _Rect(self.x, self.y, self.width + width, self.height + height)


class _Image:
    def __init__(self, name: str, width: int, height: int) -> None:
        self.name = name
        self.width = width
        self.height = height

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_size(self):
        return self.width, self.height

    def get_rect(self, **kwargs):
        return _Rect(0, 0, self.width, self.height, **kwargs)

    def subsurface(self, rect):
        return _Image(f"{self.name}:frame-{rect.x // max(1, rect.width)}", rect.width, rect.height)

    def copy(self):
        return self


class _Surface:
    def __init__(self) -> None:
        self.blits = []

    def blit(self, image, rect) -> None:
        self.blits.append((image, rect))


class _Font:
    def render(self, _text, _aa, _color):
        return _Image("badge", 10, 10)


def _fake_pygame(rotate_calls, flip_calls=None):
    if flip_calls is None:
        flip_calls = []
    return SimpleNamespace(
        Rect=_Rect,
        draw=SimpleNamespace(rect=lambda *_args, **_kwargs: None, line=lambda *_args, **_kwargs: None),
        transform=SimpleNamespace(
            scale=lambda image, size: _Image(f"{image.name}:scaled", *size),
            rotate=lambda image, angle: rotate_calls.append(angle) or image,
            flip=lambda image, horizontal, vertical: flip_calls.append((horizontal, vertical)) or image,
        ),
        font=SimpleNamespace(Font=lambda *_args: _Font()),
    )


def make_tower(*, facing: Facing = Facing.DOWN, attacking: bool = False) -> TowerRuntime:
    return TowerRuntime(
        identifier="tower-1",
        request=BuildRequest(TowerKind.ARCHER_2, (1, 1), Vector2(100, 100)),
        level=1,
        priority=TargetPriority.NEAREST,
        facing=facing,
        attack_animation_remaining=0.1 if attacking else 0.0,
    )


def test_renderer_extracts_one_base_frame_and_places_archer_on_platform(monkeypatch) -> None:
    rotate_calls = []
    monkeypatch.setitem(sys.modules, "pygame", _fake_pygame(rotate_calls))

    base_sheet = _Image("base-sheet", 280, 130)
    unit_sheet = _Image("unit-sheet", 192, 48)

    def fake_load_image(path):
        if path == TOWER_IDLE_ASSETS[TowerKind.ARCHER_2]:
            return base_sheet
        if path == TOWER_UNIT_SHEETS[TowerKind.ARCHER_2]:
            return unit_sheet
        return None

    monkeypatch.setattr("towers.sprites.load_image", fake_load_image)
    surface = _Surface()

    TowerRenderer().draw_tower(surface, make_tower())

    base_image, base_rect = surface.blits[0]
    unit_image, unit_rect = surface.blits[1]
    assert base_image.name.startswith("base-sheet:frame-")
    assert base_image.get_size() == (70, 130)
    assert unit_image.get_size() == (48, 48)
    assert base_rect.midbottom == (100, 132)
    assert unit_rect.midbottom == (100, 84)
    assert unit_rect.midbottom[1] < base_rect.midbottom[1]


def test_renderer_uses_side_attack_sheet_and_mirrors_it_for_right(monkeypatch) -> None:
    rotate_calls = []
    flip_calls = []
    monkeypatch.setitem(sys.modules, "pygame", _fake_pygame(rotate_calls, flip_calls))

    base_sheet = _Image("base-sheet", 280, 130)
    side_attack = _Image("side-attack", 192, 48)
    requested_side_attack = TOWER_UNIT_SHEETS[TowerKind.ARCHER_2].with_name("side_attack.png")

    def fake_load_image(path):
        if path == TOWER_IDLE_ASSETS[TowerKind.ARCHER_2]:
            return base_sheet
        if path == requested_side_attack:
            return side_attack
        return None

    monkeypatch.setattr("towers.sprites.load_image", fake_load_image)
    surface = _Surface()

    TowerRenderer().draw_tower(surface, make_tower(facing=Facing.RIGHT, attacking=True))

    assert surface.blits[1][0].name.startswith("side-attack:frame-")
    assert flip_calls == [(True, False)]


def test_renderer_uses_side_sheet_without_mirroring_for_left(monkeypatch) -> None:
    rotate_calls = []
    flip_calls = []
    monkeypatch.setitem(sys.modules, "pygame", _fake_pygame(rotate_calls, flip_calls))

    base_sheet = _Image("base-sheet", 280, 130)
    side_idle = _Image("side-idle", 192, 48)
    requested_side_idle = TOWER_UNIT_SHEETS[TowerKind.ARCHER_2].with_name("side_idle.png")

    def fake_load_image(path):
        if path == TOWER_IDLE_ASSETS[TowerKind.ARCHER_2]:
            return base_sheet
        if path == requested_side_idle:
            return side_idle
        return None

    monkeypatch.setattr("towers.sprites.load_image", fake_load_image)
    surface = _Surface()

    TowerRenderer().draw_tower(surface, make_tower(facing=Facing.LEFT))

    assert surface.blits[1][0].name.startswith("side-idle:frame-")
    assert flip_calls == []


def test_attack_uses_preattack_before_falling_back_to_idle(monkeypatch) -> None:
    rotate_calls = []
    monkeypatch.setitem(sys.modules, "pygame", _fake_pygame(rotate_calls))

    base_sheet = _Image("base-sheet", 280, 130)
    side_preattack = _Image("side-preattack", 192, 48)
    requested_side_preattack = TOWER_UNIT_SHEETS[TowerKind.ARCHER_2].with_name("side_preattack.png")

    def fake_load_image(path):
        if path == TOWER_IDLE_ASSETS[TowerKind.ARCHER_2]:
            return base_sheet
        if path == requested_side_preattack:
            return side_preattack
        return None

    monkeypatch.setattr("towers.sprites.load_image", fake_load_image)
    surface = _Surface()

    TowerRenderer().draw_tower(surface, make_tower(facing=Facing.LEFT, attacking=True))

    assert surface.blits[1][0].name.startswith("side-preattack:frame-")


def test_arrow_keeps_thin_aspect_ratio_and_uses_upward_source_offset(monkeypatch) -> None:
    rotate_calls = []
    monkeypatch.setitem(sys.modules, "pygame", _fake_pygame(rotate_calls))

    arrow = _Image("arrow", 3, 14)
    monkeypatch.setattr(
        "towers.sprites.load_image",
        lambda path: arrow if path == ARROW_SHEET else None,
    )
    projectile = Projectile(
        identifier="arrow-1",
        source_id="tower-1",
        target_id="enemy-1",
        position=Vector2(50, 50),
        damage=1,
        speed=1,
        extra_pierces_remaining=0,
        splash_radius=0,
        splash_damage_multiplier=1,
        lifetime_remaining=1,
        remaining_travel_distance=1,
        direction=Vector2(0, -1),
    )
    surface = _Surface()

    TowerRenderer().draw_projectile(surface, projectile)

    rendered_arrow = surface.blits[0][0]
    assert rendered_arrow.get_size() == (5, 22)
    assert rotate_calls == [0.0]
