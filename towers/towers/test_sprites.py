from __future__ import annotations

import sys
from types import SimpleNamespace

from shared.contracts import BuildRequest, TowerKind, Vector2
from shared.asset_manifest import ARROW_SHEET, TOWER_IDLE_ASSETS, TOWER_UNIT_SHEETS
from towers.models import Projectile, TargetPriority, TowerRuntime
from towers.sprites import TowerRenderer


class _Rect:
    def __init__(self, x=0, y=0, width=0, height=0, **kwargs) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = kwargs.get("center", (x + width // 2, y + height // 2))

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


def _fake_pygame(rotate_calls):
    return SimpleNamespace(
        Rect=_Rect,
        draw=SimpleNamespace(rect=lambda *_args, **_kwargs: None, line=lambda *_args, **_kwargs: None),
        transform=SimpleNamespace(
            scale=lambda image, size: _Image(f"{image.name}:scaled", *size),
            rotate=lambda image, angle: rotate_calls.append(angle) or image,
        ),
        font=SimpleNamespace(Font=lambda *_args: _Font()),
    )


def test_renderer_extracts_one_base_frame_and_keeps_pixel_dimensions(monkeypatch) -> None:
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
    tower = TowerRuntime(
        identifier="tower-1",
        request=BuildRequest(TowerKind.ARCHER_2, (1, 1), Vector2(100, 100)),
        level=1,
        priority=TargetPriority.NEAREST,
    )
    surface = _Surface()

    TowerRenderer().draw_tower(surface, tower)

    assert surface.blits[0][0].name.startswith("base-sheet:frame-")
    assert surface.blits[0][0].get_size() == (70, 130)
    assert surface.blits[1][0].get_size() == (48, 48)


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
