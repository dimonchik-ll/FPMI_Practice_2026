from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path("settings.json")


def _clamp_percent(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default

    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    return max(0, min(100, number))


def _read_bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


@dataclass(slots=True)
class MenuSettings:
    sound_enabled: bool = True
    music_enabled: bool = True
    sound_volume: int = 80
    music_volume: int = 70
    show_menu_hints: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "MenuSettings":
        defaults = cls()

        return cls(
            sound_enabled=_read_bool(
                data.get("sound_enabled"),
                defaults.sound_enabled,
            ),
            music_enabled=_read_bool(
                data.get("music_enabled"),
                defaults.music_enabled,
            ),
            sound_volume=_clamp_percent(
                data.get("sound_volume"),
                defaults.sound_volume,
            ),
            music_volume=_clamp_percent(
                data.get("music_volume"),
                defaults.music_volume,
            ),
            show_menu_hints=_read_bool(
                data.get("show_menu_hints"),
                defaults.show_menu_hints,
            ),
        )

    def to_mapping(self) -> dict[str, bool | int]:
        return asdict(self)


def load_settings(path: Path = SETTINGS_PATH) -> MenuSettings:
    if not path.exists():
        return MenuSettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return MenuSettings()

    if not isinstance(data, dict):
        return MenuSettings()

    return MenuSettings.from_mapping(data)


def save_settings(
    settings: MenuSettings,
    path: Path = SETTINGS_PATH,
) -> None:
    path.write_text(
        json.dumps(
            settings.to_mapping(),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
