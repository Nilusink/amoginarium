"""
_sound_effect.py
29.03.2026

dummy for playing a sound effect, sends command instead of creating a sound

Author:
Nilusink
"""

from amoginarium import pv
from amoginarium.shared import ProcessCommand, ProcessCommandType


class GraphicsSoundEffect:
    """graphics sound effect dummy"""

    volume: float = 1

    def __init__(self, sound: str | tuple[str, str]) -> None:
        self._sound_name = sound

    def play(
        self,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
    ) -> None:
        """Send command to play sound"""
        pv.COQ.put(
            ProcessCommand(
                type=ProcessCommandType.play_sound,
                kwargs={
                    "loops": loops,
                    "maxtime": maxtime,
                    "fade_ms": fade_ms,
                    "sound_name": self._sound_name,
                },
            )
        )


class PresetGraphicsSoundEffect(GraphicsSoundEffect):
    _sound_name: str

    def __init__(self):
        super().__init__(self._sound_name)
