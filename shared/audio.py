from __future__ import annotations

from pathlib import Path
from typing import Final

import pygame

from ui.settings import SETTINGS_PATH, MenuSettings, load_settings

_AUDIO_ROOT: Final = Path("assets/audio")
_MENU_MUSIC_PATH: Final = _AUDIO_ROOT / "music" / "main_menu_music.mp3"
_GAME_MUSIC_PATH: Final = _AUDIO_ROOT / "music" / "game_music.mp3"
_BOW_SOUND_PATH: Final = _AUDIO_ROOT / "sfx" / "bow_sound.mp3"
_FIREBALL_SOUND_PATH: Final = _AUDIO_ROOT / "sfx" / "fireball_sound.mp3"


class AudioSystem:
    """Small wrapper around pygame.mixer for menu music and tower shots."""

    def __init__(self) -> None:
        self._available = self._init_mixer()
        self._settings = load_settings()
        self._settings_mtime = self._settings_modified_time()
        self._current_music: Path | None = None
        self._bow_sound: pygame.mixer.Sound | None = None
        self._fireball_sound: pygame.mixer.Sound | None = None

        if self._available:
            self._bow_sound = self._load_sound(_BOW_SOUND_PATH)
            self._fireball_sound = self._load_sound(_FIREBALL_SOUND_PATH)
            self._apply_settings()

    def play_menu_music(self) -> None:
        self._play_music(_MENU_MUSIC_PATH)

    def play_game_music(self) -> None:
        self._play_music(_GAME_MUSIC_PATH)

    def play_tower_shot(self, projectile_kind: str) -> None:
        if not self._available:
            return

        self.refresh_settings()

        if not self._settings.sound_enabled:
            return

        sound = self._fireball_sound if projectile_kind == "fireball" else self._bow_sound

        if sound is not None:
            sound.play()

    def refresh_settings(self) -> None:
        if not self._available:
            return

        current_mtime = self._settings_modified_time()

        if current_mtime == self._settings_mtime:
            return

        self._settings_mtime = current_mtime
        self._settings = load_settings()
        self._apply_settings()

    def stop(self) -> None:
        if self._available:
            pygame.mixer.music.stop()
            self._current_music = None

    @staticmethod
    def _init_mixer() -> bool:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            return False

        return True

    @staticmethod
    def _settings_modified_time() -> float | None:
        try:
            return SETTINGS_PATH.stat().st_mtime
        except OSError:
            return None

    @staticmethod
    def _load_sound(path: Path) -> pygame.mixer.Sound | None:
        if not path.exists():
            return None

        try:
            return pygame.mixer.Sound(str(path))
        except pygame.error:
            return None

    def _play_music(self, path: Path) -> None:
        if not self._available:
            return

        self.refresh_settings()

        if self._current_music == path:
            if self._settings.music_enabled:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()
            return

        if not path.exists():
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(-1)
        except pygame.error:
            return

        self._current_music = path
        self._apply_settings()

    def _apply_settings(self) -> None:
        music_volume = self._volume(self._settings.music_volume)
        sound_volume = self._volume(self._settings.sound_volume)

        pygame.mixer.music.set_volume(music_volume)

        if self._settings.music_enabled:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        for sound in (self._bow_sound, self._fireball_sound):
            if sound is not None:
                sound.set_volume(sound_volume)

    @staticmethod
    def _volume(percent: int) -> float:
        return max(0.0, min(1.0, percent / 100.0))
