"""
_background.py
22. March 2024

background music

Author:
Nilusink
"""
from random import randint
import pygame as pg

from ._sounds import sounds


class BackgroundPlayer:
    def __init__(self) -> None:
        self._sound_files: list[pg.mixer.Sound] = []
        self._playing: pg.Channel = ...
        self.volume = 1

    def assign_scope(self, scope: str) -> None:
        """
        select a scope to play background songs from
        """
        for sound in sounds.get_all_from_scope(scope):
            self._sound_files.append(sound)

    def play_track(self, id: int) -> None:
        if len(self._sound_files) <= id:
            raise ValueError

        sound = self._sound_files[id]
        sound.set_volume(self.volume)
        self._playing = sound.play(loops=-1, fade_ms=5000)

    def start(self) -> None:
        sound = self._sound_files[
            randint(0, len(self._sound_files) - 1)
        ]
        sound.set_volume(self.volume)
        self._playing = sound.play(loops=-1, fade_ms=5000)

    def update(self) -> None:
        """
        checks if the sound is done and plays another one
        """
        if self._playing is ... or not self._playing.get_busy():
            self.start()
