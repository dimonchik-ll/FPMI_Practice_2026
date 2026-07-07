# Удаление башен в основном приложении

В архиве только два изменённых файла:

- `integration/app.py` — правый клик по башне удаляет её через `TowerSystem.remove_at_position(...)`, затем освобождает место на карте;
- `core/game_shell.py` — добавлен `CoreWorld.release_tower_cell(cell)`.

`core/map_model.py` заменять не нужно: в текущем проекте `GameMap.release(cell)` уже существует и корректно освобождает все 4 клетки `tower_spot`.

## Установка

Распаковать архив в корень репозитория с заменой файлов:

```bash
unzip -o tower_deletion_integration.zip -d .
```

Затем запустить:

```bash
python -m pytest -q
python team_launcher.py
```

## Требование

В папке `towers/` уже должна быть версия с методами:

```python
TowerSystem.remove_at_position(position)
TowerSystem.remove_at_cell(cell)
```

Иначе `integration/app.py` не сможет вызвать удаление.

Удаление не возвращает деньги игроку: это отдельное правило экономики, которого в этом изменении нет.
