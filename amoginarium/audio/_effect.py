"""
_effect.py
22. March 2024

a basic sound effect

Author:
Nilusink
"""
from icecream import ic
from ._sounds import sounds, sound_name_t
import typing as tp
import pygame as pg

from ..debugging import run_with_debug


class _SoundEffects:
    """
    a collection of all sound effects
    """
    def __init__(self) -> None:
        self._effects = []

    def add(self, effect: "SoundEffect") -> None:
        """
        add a sound effect to the queue
        """
        self._effects.append(effect)

    def remove(self, effect: "SoundEffect") -> None:
        """
        remove a sound effect from the queue
        """
        self._effects.remove(effect)

    def update(self) -> None:
        """
        update all sound effects
        """
        for effect in self._effects:
            effect.update()


sound_effects = _SoundEffects()


class SoundEffect:
    volume: float = 1

    def __new__(cls, *args, **kwargs):
        instance = super(SoundEffect, cls).__new__(cls)
        sound_effects.add(instance)
        return instance

    def __init__(
            self,
            sound_name: sound_name_t,
            on_finish_playing: tp.Callable[[], None] = ...
    ) -> None:
        self._sound_name = sound_name
        self._on_finish = on_finish_playing
        self._channel = ...
        self._has_played = False
        self._loop = False

        if isinstance(self._sound_name, tuple):
            self._sound = sounds.get_sound(*self._sound_name[::-1])

        else:
            self._sound = sounds.get_sound(self._sound_name)

        if self._sound is None:
            raise RuntimeError(f"Sound {self._sound_name} not found!")

    @property
    def playing(self) -> bool:
        return self._has_played or self._loop

    def play(
            self,
            loops: int = 0,
            maxtime: int = 0,
            fade_ms: int = 0,
    ) -> None:
        """
        play the sound effect
        """
        if loops < 0:
            self._loop = True

        self._sound.set_volume(self.volume)
        self._channel = pg.mixer.find_channel(force=False)
        self._channel.play(self._sound, loops, maxtime, fade_ms)
        self._has_played = True

    # @run_with_debug()
    def stop(self) -> None:
        """
        stop the sound effect if it is currently playing
        """
        if self._channel is not ...:
            if self._channel.get_busy():
                self._channel.stop()

        self._has_played = False
        self._loop = False
        self._channel = ...

    def update(self) -> None:
        """
        updates called by the game loop
        """
        if self._channel is ...:
            return

        done_playing = all([
            self._has_played,
            not self._loop,
            self._on_finish is not ...,
            not self._channel.get_busy(),
        ])
        if done_playing:
            self._channel = ...
            self._on_finish()
            self.stop()


class PresetEffect(SoundEffect):
    _sound_name: str

    def __init__(self):
        super().__init__(self._sound_name)


class LargeExplosion(PresetEffect):
    _sound_name = "explosion_large"


class SmallExplosion(PresetEffect):
    _sound_name = "explosion_small"


class Shotgun(PresetEffect):
    volume = .5
    _sound_name = "shotgun"


def sound_effect_wrapper(sound_name: str, volume: float = 1) -> SoundEffect:
    """
    returns an already set sound effect
    """
    effect = SoundEffect(sound_name)
    effect.volume = volume
    return effect


# class ThreeStageSoundEffect:
#     _stage_one_name: sound_name_t
#     _stage_two_name: sound_name_t
#     _stage_three_name: sound_name_t
#     volume: float = 1
#
#     def __init__(self) -> None:
#         self._stage_one = ...
#         self._stage_two = ...
#         self._stage_three = ...
#
#         if self._stage_one_name is not ...:
#             self._stage_one = SoundEffect(
#                 self._stage_one_name,
#                 self._play_2
#             )
#             self._stage_one.volume = self.volume
#
#         if self._stage_two_name is not ...:
#             self._stage_two = SoundEffect(
#                 self._stage_two_name,
#                 self._play_3,
#                 True
#             )
#             self._stage_two.volume = self.volume
#
#         if self._stage_three_name is not ...:
#             self._stage_three = SoundEffect(
#                 self._stage_three_name,
#                 self.stop
#             )
#             self._stage_three.volume = self.volume
#
#         self._playing = False
#
#     @property
#     def playing(self) -> bool:
#         return self._playing
#
#     @run_with_debug()
#     def play(self) -> None:
#         """
#         play the sound effect
#         """
#         self._playing = True
#         if self._stage_one is not ...:
#             self._stage_one.play()
#
#         else:
#             self._play_2()
#
#     @run_with_debug()
#     def _play_2(self) -> None:
#         if self._playing:
#             if not self._stage_two.playing:
#                 self._stage_two.play()
#
#     def _play_3(self, force_play: bool = False) -> None:
#         if self._playing or force_play:
#             if self._stage_three is not ...:
#                 self._stage_three.play()
#
#     @run_with_debug()
#     def stop(self) -> None:
#         """
#         stop the sound effect from playing
#         """
#         self._playing = False
#
#
# class ContinuousSoundEffect(ThreeStageSoundEffect):
#     _stage_one_name = ...
#     _stage_three_name = ...
#
#     def __init__(self) -> None:
#         super().__init__()
#         # self._stage_two = SoundEffect(
#         #     self._stage_two_name,
#         # )
#         # self._stage_two.volume = self.volume
#         self._one_done = self._stage_one_name is ...
#
#     @property
#     def stage_one_done(self) -> bool:
#         return self._one_done
#
#     @run_with_debug()
#     def play(self) -> None:
#         self._one_done = False
#         super().play()
#
#     @run_with_debug()
#     def _play_2(self) -> None:
#         self._one_done = True
#
#         ic(0)
#         ic(self._playing, self._stage_two.playing)
#         if self._playing and not self._stage_two.playing:
#             ic(1)
#             self._stage_two.play(-1)
#             ic(2)
#
#     def _play_3(self, force_play: bool = False) -> None:
#         pass
#
#     @run_with_debug()
#     def done(self) -> None:
#         """
#         stop stage 2 playing
#         """
#         self._stage_two.stop()
#
#         if self.stage_one_done and self._playing:
#             super()._play_3(True)
#             self.stop()
#
#     @run_with_debug()
#     def stop(self) -> None:
#         self._playing = False
#         self._stage_two.stop()


class ContinuousSoundEffect:
    _stage_one_name: str = ...
    _stage_two_name: str = ...
    _stage_three_name: str = ...

    def __init__(self, volume: float = 1) -> None:
        self._stage_one = ...
        self._stage_two = ...
        self._stage_three = ...

        if self._stage_one_name is not ...:
            self._stage_one = SoundEffect(
                self._stage_one_name,
                self._play_2
            )

        if self._stage_two_name is not ...:
            self._stage_two = SoundEffect(
                self._stage_two_name,
                self._play_3
            )

        if self._stage_three_name is not ...:
            self._stage_three = SoundEffect(
                self._stage_three_name,
                self._stop
            )

        self.volume = volume
        self._playing = 0

        ic(self._stage_one, self._stage_two, self._stage_three)

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, volume: float) -> None:
        self._volume = volume
        if self._stage_one is not ...:
            self._stage_one.volume = self._volume

        if self._stage_two is not ...:
            self._stage_two.volume = self._volume

        if self._stage_three is not ...:
            self._stage_three.volume = self._volume

    @property
    def playing(self) -> int:
        return self._playing

    @property
    def stage_one_done(self) -> bool:
        return self.playing > 1

    @run_with_debug()
    def play(self) -> None:
        if self._stage_one is ...:
            return self._play_2()

        self._playing = 1
        self._stage_one.play()

    @run_with_debug()
    def _play_2(self) -> None:
        if self._stage_two is ...:
            return self._play_3()

        self._playing = 2
        self._stage_two.play(loops=-1)

    @run_with_debug()
    def _play_3(self) -> None:
        if self._stage_three is ...:
            return self._stop()

        self._playing = 3
        self._stage_three.play()

    @run_with_debug()
    def stop(self) -> None:
        match self.playing:
            case 1:
                self._stage_one.stop()
            case 2:
                self._stage_two.stop()
            case 3:
                self._stage_three.stop()

        return self._stop()

    @run_with_debug()
    def _stop(self) -> None:
        self._playing = 0

    @run_with_debug()
    def done(self) -> None:
        """
        stop loop and play shutdown
        """
        match self.playing:
            case 1:
                self._stage_one.stop()
                self._stage_two.stop()
            case 2:
                self._stage_two.stop()
            case 3:
                return

        self._play_3()


class Minigun(ContinuousSoundEffect):
    _stage_one_name = "spool_up"
    _stage_two_name = "burst"
    _stage_three_name = "spool_down"
    volume: float = .1


class AK47(ContinuousSoundEffect):
    _stage_two_name = ("ak47", "loop")
    volume: float = .1
