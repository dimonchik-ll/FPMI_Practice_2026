# Team scaffold для Tower Defense

Этот набор добавляет независимые модули для четырёх разработчиков. Базовая игра запускается через:

```bash
python team_launcher.py
```

Установка:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python tools/import_assets.py --tiles /путь/tiles.zip --enemies /путь/enemies.zip --towers /путь/towers.zip
python -m pytest -q
python team_launcher.py
```

Подробный план и договорённости: [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md).
