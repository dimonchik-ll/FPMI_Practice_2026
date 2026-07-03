# Разработчик 1 — core

В этой папке находятся карта, путь, координаты клеток и базовая игровая сцена.

Можно менять только `core/` и `assets/tiles/`.

Контракт для других модулей нельзя ломать:

- `GameMap.build_route() -> tuple[Vector2, ...]`
- `GameMap.world_to_cell(position) -> GridCell`
- `GameMap.is_buildable(cell) -> bool`
- `CoreWorld.create_build_request(cell, tower_kind) -> BuildRequest | None`

Проверка: `python -m core.sandbox`.
