# Ассеты

После применения patch запусти импортёр:

```bash
python tools/import_assets.py \
  --tiles /путь/к/craftpix_net_665131_free_fields_tileset_pixel_art_for_tower_defense.zip \
  --enemies /путь/к/craftpix-net-255707-free-field-enemies-pixel-art-for-tower-defense.zip \
  --towers /путь/к/craftpix-net-658475-free-archer-towers-pixel-art-for-tower-defense.zip
```

Он создаст папки `tiles/`, `towers/`, `enemies/`, `projectiles/` и `licenses/` с предсказуемыми именами. Без импортированных PNG игра использует простые геометрические заглушки, поэтому разработка модулей не блокируется.

Файлы лицензий из исходных архивов копируются в `assets/licenses/`. Перед публикацией игры проверь условия использования в этих файлах.
