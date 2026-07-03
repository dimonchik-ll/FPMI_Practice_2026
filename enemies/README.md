# Разработчик 3 — enemies

Можно менять только `enemies/` и `assets/enemies/`.

Модуль врагов не импортирует `towers/`. Он принимает `list[DamageCommand]` в `EnemySystem.apply_damage`, а наружу отдаёт `tuple[EnemyView, ...]` и `list[GameEvent]`.

Текущий код поддерживает маршрут, очереди волн, получение урона, награды и достижение базы.

Проверка: `python -m enemies.sandbox`.
