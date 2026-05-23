"""
Manages spatialized audio effects, sound playback, and preset sound classes.

| Path: amoginarium/shared/audio/_effect.py
| Project: amoginarium
| Created: 22.03.2024
| Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import math as m
import typing as tp
from random import choices, uniform
from types import EllipsisType

import pygame as pg
from icecream import ic

from amoginarium import pv
from amoginarium.shared.debugging import CC
from amoginarium.shared.utility import Vec2

from ._sounds import sounds

if tp.TYPE_CHECKING:
    from ._sounds import sound_name_t

# --- CONFIG ---
MAX_DIST = 6000.0
MIN_DIST = 1.0


def spatialize(
    channel: pg.mixer.Channel, delta: Vec2, base_volume: float = 1.0
) -> None:
    """Set a channel's volume based on direction + distance + base volume."""
    # --- clamp base volume ---
    base_volume = max(0.0, min(base_volume, 1.0))

    # --- get params ---
    distance = max(delta.length, MIN_DIST)
    a = delta.angle  # radians

    # --- normalize distance (0..1) ---
    d_norm = min(max(distance / MAX_DIST, 0.0), 1.0)

    # --- FIX 1: correct angle reference (forward = 0) ---
    a -= m.pi / 2

    # --- FIX 2: proper pan calculation (-1 .. 1) ---
    pan = -m.sin(a)

    # --- equal-power panning ---
    left = m.sqrt((1 - pan) / 2)
    right = m.sqrt((1 + pan) / 2)

    # --- stereo width (distance-dependent) ---
    width = m.sqrt(d_norm)

    center = 0.707  # equal-power center

    left = (1 - width) * center + width * left
    right = (1 - width) * center + width * right

    # --- distance attenuation ---
    falloff = 1 / (1 + 4 * d_norm**1.5)

    # --- combine everything ---
    gain = base_volume * falloff

    # --- final apply ---
    channel.set_volume(left * gain, right * gain)


class _SoundEffects:
    """
    a collection of all sound effects.
    """

    def __init__(self) -> None:
        self._effects = []

    def add(self, effect: SoundEffect) -> None:
        """
        Add a sound effect to the queue.
        """
        self._effects.append(effect)

    def remove(self, effect: SoundEffect) -> None:
        """
        Remove a sound effect from the queue.
        """
        self._effects.remove(effect)

    def update(self) -> None:
        """
        Update all sound effects.
        """
        for effect in self._effects:
            effect.update()


sound_effects = _SoundEffects()


class SoundEffect:
    """sound effect."""

    volume: float = 1

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        sound_effects.add(instance)
        return instance

    def __init__(
        self,
        sound: sound_name_t | pg.mixer.Sound,
        on_finish_playing: tp.Callable[[], tp.Any] | EllipsisType = ...,
    ) -> None:
        self._sound_name = sound
        self._on_finish = on_finish_playing
        self._channel: pg.mixer.Channel | EllipsisType = ...
        self._has_played = False
        self._loop = False
        self._pos: Vec2 | EllipsisType = ...
        self._sound = ...

    @property
    def playing(self) -> bool:
        """Check if the sound effect is currently playing."""
        return self._has_played or self._loop

    def set_volume(self, volume: float) -> tp.Self:
        """Set the sound-effects volume."""
        self.volume = volume
        return self

    def play(
        self,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
        pos: Vec2 | EllipsisType = ...,
    ) -> None:
        """
        Play the sound effect.
        """
        if loops < 0:
            self._loop = True

        if pos is not ...:
            self._pos = pos

        self._update_volume()
        if self._has_played and not self._loop:
            SoundEffect(self._sound_name, self._on_finish).set_volume(self.volume).play(
                loops, maxtime, fade_ms, pos
            )
            return

        if isinstance(self._sound_name, pg.mixer.Sound):
            self._sound = self._sound_name

        elif isinstance(self._sound_name, (tuple, list)):
            self._sound = sounds.get_sound(*self._sound_name[::-1])

        else:
            self._sound = sounds.get_sound(self._sound_name)

        if self._sound is None:
            msg = f"Sound {self._sound_name} not found!"
            raise RuntimeError(msg)

        self._channel = pg.mixer.find_channel(force=False)
        if self._channel is None:
            return

        self._channel.play(self._sound, loops, maxtime, fade_ms)
        self._has_played = True

    def update_position(self, pos: Vec2) -> None:
        """Update the sounds current position."""
        if isinstance(self._pos, EllipsisType):
            self._pos = Vec2()

        self._pos.xy = pos.xy

    def stop(self) -> None:
        """
        Stop the sound effect if it is currently playing.
        """
        if self._channel is not ... and self._channel is not None:
            if self._channel.get_busy():
                self._channel.stop()

        self._has_played = False
        self._loop = False
        self._channel = ...

    def _update_volume(self) -> None:
        """Adjust the volume depending on position."""
        if self._channel is ... or self._channel is None:
            return

        # set volume
        self._channel.set_volume(self.volume)

        if self._pos is ...:
            return

        # set distance / angle
        if self._channel.get_busy():
            delta = self._pos - pv.audio_observer_pos
            spatialize(self._channel, delta, self.volume)

    def update(self) -> None:
        """
        Updates called by the game loop.
        """
        if self._channel is ... or self._channel is None:
            return

        self._update_volume()

        done_playing = all(
            [
                self._has_played,
                not self._loop,
                not self._channel.get_busy(),
            ]
        )
        if done_playing:
            self._channel = ...
            if self._on_finish is not ...:
                self._on_finish()

            self.stop()


class PresetEffect(SoundEffect):
    """preset sound effect."""

    _sound_name: str | tuple[str, str]

    def __init__(self) -> None:
        super().__init__(self._sound_name)


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


class Sniper(PresetEffect):
    volume = 1
    _sound_name = ("shots", "sniper")


class ReloadGeneric(PresetEffect):
    volume = 0.4
    _sound_name = "reload_generic"


class OnHoverButtonSound(PresetEffect):
    volume = 1
    _sound_name = "button_hover"


class RocketSound(PresetEffect):
    volume = 1
    _sound_name = ("rocket", "jetbag")


def sound_effect_wrapper(sound_name: str, volume: float = 1) -> SoundEffect:
    """
    Returns an already set sound effect.
    """
    effect = SoundEffect(sound_name)
    effect.volume = volume
    return effect


class ContinuousSoundEffect:
    """sound effect with three stages."""

    _stage_one_name: str = ...
    _stage_two_name: str = ...
    _stage_three_name: str = ...

    def __init__(self, volume: float = 1) -> None:
        self._stage_one = ...
        self._stage_two = ...
        self._stage_three = ...
        self._pos = ...

        if self._stage_one_name is not ...:
            self._stage_one = SoundEffect(self._stage_one_name, self._play_2)

        if self._stage_two_name is not ...:
            self._stage_two = SoundEffect(self._stage_two_name, self._play_3)

        if self._stage_three_name is not ...:
            self._stage_three = SoundEffect(self._stage_three_name, self._stop)

        self.volume = volume
        self._playing = 0

    @property
    def volume(self) -> float:
        """The sounds volume."""
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
        """Check which stage the sound is currently playing (0 if None)."""
        return self._playing

    @property
    def stage_one_done(self) -> bool:
        """Check if the first stage of the sound effect is done."""
        return self.playing > 1

    def play(self, pos: Vec2 | EllipsisType = ...) -> None:
        """Play the sound."""
        self._pos = pos

        if self._playing:
            info = CC.fg.RED + "tried to double-play CSE" + CC.ctrl.ENDC
            ic(info)
            return

        if self._stage_one is ...:
            self._play_2()
            return

        self._playing = 1
        self._stage_one.play(pos=pos)

    def _play_2(self) -> None:
        if self._stage_two is ...:
            self._play_3()
            return

        self._playing = 2
        self._stage_two.play(loops=-1, pos=self._pos)

    def _play_3(self) -> None:
        if self._stage_three is ...:
            self._stop()
            return

        self._playing = 3
        self._stage_three.play(pos=self._pos)

    def stop(self) -> None:
        """Stop playing the sound (except last stage)."""
        match self.playing:
            case 1:
                self._stage_one.stop()
            case 2:
                self._stage_two.stop()

        self._stop()

    def _stop(self) -> None:
        self._playing = 0

    def done(self) -> None:
        """
        Stop loop and play shutdown.
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
    volume: float = 0.1


class CRAM(ContinuousSoundEffect):
    # _stage_one_name = ("minigun", "spool_up_short")
    _stage_two_name = ("minigun", "burst")
    _stage_three_name = ("minigun", "spool_down")
    volume: float = 0.1


class PotionDrink(ContinuousSoundEffect):
    _stage_two_name = ("potion_drink", "loop")
    _stage_three_name = ("potion_drink", "finish")


class RandomizedEffect:
    """sound effect but random."""

    _default_weights: tuple[float, ...] | EllipsisType = ...
    _default_volumes: tuple[float, ...] | EllipsisType = ...

    def __init__(
        self,
        effects: tp.Sequence[SoundEffect],
        weights: tuple[float, ...] | None = None,
        volumes: tuple[float, ...] | None = None,
    ) -> None:
        self._effects = effects
        self._playing = None
        self._max_volume = 1
        self._min_volume = 1

        self._weights: tuple[float, ...] = ()
        if weights:
            self._weights = weights

        elif isinstance(self._default_weights, EllipsisType):
            self._weights = (1,) * len(effects)

        else:
            self._weights = self._default_weights

        self._volumes: tuple[float, ...] = ()
        if volumes:
            self._volumes = volumes

        elif isinstance(self._default_volumes, EllipsisType):
            self._volumes = (1,) * len(effects)

        else:
            self._volumes = self._default_volumes

    @property
    def playing(self) -> bool:
        """Check if the sound is playing."""
        return bool(self._playing)

    @property
    def volume(self) -> int:
        """Set the sounds max volume."""
        return self._max_volume

    @volume.setter
    def volume(self, volume: float) -> None:
        self._max_volume = volume * 1.1
        self._min_volume = volume * 0.9

    def set_volume(self, max_volume: float, min_volume: float) -> tp.Self:
        """Set volume range."""
        self._max_volume = max_volume
        self._min_volume = min_volume

        return self

    def play(
        self,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
        pos: Vec2 | EllipsisType = ...,
    ) -> None:
        """
        Play the sound effect.
        """
        # if self._playing:
        #     self.stop()

        # get sound from list (with weights)
        self._playing = choices(self._effects, weights=self._weights, k=1)[0]

        # add volume factor
        volume_fac = self._volumes[self._effects.index(self._playing)]
        self._playing.volume = uniform(self._min_volume, self._max_volume) * volume_fac

        self._playing.play(loops, maxtime, fade_ms, pos)

    def stop(self) -> None:
        """
        Stop the sound effect if it is currently playing.
        """
        if self._playing:
            self._playing.stop()
            self._playing = None

    def update(self) -> None:
        """
        Updates called by the game loop.
        """
        if self._playing:
            self._playing.update()


class ScopedRandomizedEffect(RandomizedEffect):
    _scope: str | None = None

    def __init__(
        self,
        sound_scope: str | None = None,
        callback: tp.Callable[[], tp.Any] | None = None,
    ) -> None:
        if sound_scope is None:
            sound_scope = self._scope
            if sound_scope is None:
                msg = "No scope given for sounds"
                raise ValueError(msg)

        s = sounds.get_all_from_scope(sound_scope)
        info = sounds.get_scope_info(sound_scope)

        weights = None
        # load weights if given
        if "weights" in info:
            weights = info["weights"]

        super().__init__(
            [SoundEffect(sound, callback or ...) for sound in s],
            weights=weights,
        )


class DeathSound(ScopedRandomizedEffect):
    def __init__(self, callback: tp.Callable[[], tp.Any] | None = None) -> None:
        super().__init__("death", callback)


class DistantPop(ScopedRandomizedEffect):
    _scope = "distant_pop"


class AK47(ScopedRandomizedEffect):
    _scope = "ak47"


class Cannon(ScopedRandomizedEffect):
    _scope = "cannon"


class MetalPings(ScopedRandomizedEffect):
    _scope = "metal_pings"


class LargeExplosion(ScopedRandomizedEffect):
    _scope = "explosion_large"


PRESETS: dict[str, type[SoundEffect | ContinuousSoundEffect | RandomizedEffect]] = {
    "minigun": Minigun,
    "cram": CRAM,
}
