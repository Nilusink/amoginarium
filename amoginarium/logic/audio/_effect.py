"""
_effect.py
22. March 2024

a basic sound effect

Author:
Nilusink
"""

from random import choice, uniform
from types import EllipsisType
from icecream import ic
import typing as tp
import pygame as pg
import math as m

from amoginarium.shared.debugging import CC
from amoginarium.shared.utility import Vec2
from amoginarium import pv

from ._sounds import sounds, sound_name_t


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
    """sound effect"""
    volume: float = 1

    def __new__(cls, *args, **kwargs):
        instance = super(SoundEffect, cls).__new__(cls)
        sound_effects.add(instance)
        return instance

    def __init__(
            self,
            sound: sound_name_t | pg.mixer.Sound,
            on_finish_playing: tp.Callable[[], tp.Any] = ...
    ) -> None:
        self._sound_name = sound
        self._on_finish = on_finish_playing
        self._channel: pg.mixer.Channel = ...
        self._has_played = False
        self._loop = False
        self._pos: Vec2 | EllipsisType = ...

    @property
    def playing(self) -> bool:
        return self._has_played or self._loop

    def set_volume(self, volume: float) -> tp.Self:
        self.volume = volume
        return self

    def play(
            self,
            loops: int = 0,
            maxtime: int = 0,
            fade_ms: int = 0,
            pos: Vec2 | EllipsisType = ...
    ) -> None:
        """
        play the sound effect
        """
        if loops < 0:
            self._loop = True

        if pos is not ...:
            self._pos = pos

        self._update_volume()
        if self._has_played and not self._loop:
            SoundEffect(
                self._sound_name,
                self._on_finish
            ).set_volume(
                self.volume
            ).play(
                loops,
                maxtime,
                fade_ms
            )
            return

        if isinstance(self._sound_name, pg.mixer.Sound):
            self._sound = self._sound_name

        elif isinstance(self._sound_name, tuple):
            self._sound = sounds.get_sound(*self._sound_name[::-1])

        else:
            self._sound = sounds.get_sound(self._sound_name)

        if self._sound is None:
            raise RuntimeError(f"Sound {self._sound_name} not found!")

        # self._sound.set_volume(self.volume)
        self._channel = pg.mixer.find_channel(force=False)
        if self._channel is None:
            return

        self._channel.play(self._sound, loops, maxtime, fade_ms)
        self._has_played = True

    def stop(self) -> None:
        """
        stop the sound effect if it is currently playing
        """
        if self._channel is not ... and self._channel is not None:
            if self._channel.get_busy():
                self._channel.stop()

        self._has_played = False
        self._loop = False
        self._channel = ...

    def _update_volume(self) -> None:
        """adjust the volume depending on position"""

        if self._channel is ... or self._channel is None:
            return

        # set volume
        self._channel.set_volume(self.volume)

        if self._pos is ...:
            return

        # set distance / angle
        if self._channel.get_busy():
            delta = self._pos - pv.audio_observer_pos

            # play both sides for close sound
            if delta.length < 32:
                delta.angle = m.pi / 2

            delta.length *= .05

            self._channel.set_source_location(
                (delta.angle + m.pi / 2) * (180/m.pi),
                min(delta.length, 255),
            )

    def update(self) -> None:
        """
        updates called by the game loop
        """
        if self._channel is ... or self._channel is None:
            return

        self._update_volume()

        done_playing = all([
            self._has_played,
            not self._loop,
            not self._channel.get_busy(),
        ])
        if done_playing:
            self._channel = ...
            if self._on_finish is not ...:
                self._on_finish()

            self.stop()


class PresetEffect(SoundEffect):
    """preset sound effect"""
    _sound_name: str

    def __init__(self):
        super().__init__(self._sound_name)


class LargeExplosion(PresetEffect):
    _sound_name = "explosion_large"


class SmallExplosion(PresetEffect):
    _sound_name = "explosion_small"


class MutedBurst(PresetEffect):
    _sound_name = "muted_burst"


class Shotgun(PresetEffect):
    volume = 1
    _sound_name = "shotgun"


class Mortar(PresetEffect):
    volume = 1
    _sound_name = "mortar"


class ReloadGeneric(PresetEffect):
    volume = .4
    _sound_name = "reload_generic"


class OnHoverButtonSound(PresetEffect):
    volume = 1
    _sound_name = "button_hover"


def sound_effect_wrapper(sound_name: str, volume: float = 1) -> SoundEffect:
    """
    returns an already set sound effect
    """
    effect = SoundEffect(sound_name)
    effect.volume = volume
    return effect


class ContinuousSoundEffect:
    _stage_one_name: str = ...
    _stage_two_name: str = ...
    _stage_three_name: str = ...

    def __init__(self, volume: float = 1) -> None:
        self._stage_one = ...
        self._stage_two = ...
        self._stage_three = ...
        self._pos = ...

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

    def play(self, pos: Vec2 = ...) -> None:
        self._pos = pos

        if self._playing:
            info = CC.fg.RED+"tried to double-play CSE"+CC.ctrl.ENDC
            ic(info)
            return

        if self._stage_one is ...:
            return self._play_2()

        self._playing = 1
        self._stage_one.play(pos=pos)

    def _play_2(self) -> None:
        if self._stage_two is ...:
            return self._play_3()

        self._playing = 2
        self._stage_two.play(loops=-1, pos=self._pos)

    def _play_3(self) -> None:
        if self._stage_three is ...:
            return self._stop()

        self._playing = 3
        self._stage_three.play(pos=self._pos)

    def stop(self) -> None:
        match self.playing:
            case 1:
                self._stage_one.stop()
            case 2:
                self._stage_two.stop()
            case 3:
                self._stage_three.stop()

        return self._stop()

    def _stop(self) -> None:
        self._playing = 0

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
    _stage_one_name = ("minigun", "spool_up")
    _stage_two_name = ("minigun", "burst")
    _stage_three_name = ("minigun", "spool_down")
    volume: float = .1


class CRAM(ContinuousSoundEffect):
    _stage_one_name = ("minigun", "spool_up_short")
    _stage_two_name = ("minigun", "burst")
    _stage_three_name = ("minigun", "spool_down")
    volume: float = .1


# class AK47(ContinuousSoundEffect):
#     _stage_two_name = ("ak47", "loop")
#     _stage_three_name = ("ak47", "echo")
#     volume: float = .1


class RandomizedEffect:
    """sound effect but random"""
    def __init__(
            self,
            effects: tp.Sequence[SoundEffect],
    ) -> None:
        self._effects = effects
        self._playing = None
        self._max_volume = 1
        self._min_volume = 1

    @property
    def playing(self) -> bool:
        return not not self._playing

    @property
    def volume(self) -> int:
        return self._max_volume

    @volume.setter
    def volume(self, volume: float) -> None:
        self._max_volume = volume * 1.1
        self._min_volume = volume * .9

    def set_volume(self, max_volume: float, min_volume: float) -> tp.Self:
        self._max_volume = max_volume
        self._min_volume = min_volume

        return self

    def play(
            self,
            loops: int = 0,
            maxtime: int = 0,
            fade_ms: int = 0,
            pos: Vec2 = ...,
    ) -> None:
        """
        play the sound effect
        """
        # if self._playing:
        #     self.stop()

        self._playing = choice(self._effects)
        self._playing.volume = uniform(self._min_volume, self._max_volume)
        self._playing.play(
            loops,
            maxtime,
            fade_ms,
            pos
        )

    def stop(self) -> None:
        """
        stop the sound effect if it is currently playing
        """
        if self._playing:
            self._playing.stop()
            self._playing = None

    def update(self) -> None:
        """
        updates called by the game loop
        """
        if self._playing:
            self._playing.update()


class ScopedRandomizedEffect(RandomizedEffect):
    _scope: str | None = None

    def __init__(
            self,
            sound_scope: str | None = None,
            callback: tp.Callable[[], tp.Any] | None = None
    ) -> None:
        if sound_scope is None:
            sound_scope = self._scope
            if sound_scope is None:
                raise ValueError("No scope given for sounds")

        s = sounds.get_all_from_scope(sound_scope)
        super().__init__([
            SoundEffect(
                sound,
                callback if callback else ...
            ) for sound in s
        ])


class DeathSound(ScopedRandomizedEffect):
    def __init__(self, callback: tp.Callable[[], tp.Any] = ...) -> None:
        super().__init__("death", callback)


class DistantPop(ScopedRandomizedEffect):
    _scope = "distant_pop"


# class PitchedRandomizedEffect(RandomizedEffect):
#     _name: tuple[str, str] | None = None
#     _pitch_set: tuple[int, ...] = (-2, 2)
#
#     _pitched_sounds: list[SoundEffect] = []
#
#     def __new__(cls, *args, **kwargs):
#         if not cls._pitched_sounds:
#             sound = sounds.get_sound(*cls._name[::-1])
#
#             cls._pitched_sounds.append(SoundEffect(sound))
#             ic(1)
#             for pitch in cls._pitch_set:
#                 cls._pitched_sounds.append(
#                     SoundEffect(pitch_shift_keep_length(sound, pitch))
#                 )
#             ic(2)
#
#         return super().__new__(cls)
#
#     def __init__(self) -> None:
#         if not self._name:
#             raise ValueError("No name given for pitched effect")
#
#         super().__init__(self._pitched_sounds)


class AK47(ScopedRandomizedEffect):
    # _name = ("ak472", "0")
    _scope = "ak472"
