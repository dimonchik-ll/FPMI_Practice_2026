# Разработчик 2 — towers

Можно менять только `towers/`, `assets/towers/` и `assets/projectiles/`.

Башни не импортируют `enemies/`. На вход в `TowerSystem.update` приходит только `tuple[EnemyView, ...]`, а результатом является `list[DamageCommand]`.

Текущий код уже умеет поставить башню и выдавать команды урона. Дальше можно добавлять:

- анимации idle/attack;
- снаряды;
- новую цель или приоритет цели;
- новые классы башен;
- улучшения.

Проверка: `python -m towers.sandbox`.
