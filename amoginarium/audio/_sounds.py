"""
_sounds.py
22. March 2024

global sounds

Author:
Nilusink
"""
from ..debugging import print_ic_style, get_fg_color
import pygame as pg
import typing as tp
import zipfile
import os


class NamedSound(tp.TypedDict):
    sound: pg.mixer.Sound
    name: str


class _Sounds:
    _sounds: dict[str, dict[str, NamedSound]]
    filetypes = ("mp3", "ogg", "wav")
    debug: int = 1

    def __init__(self) -> None:
        self._sounds = {}

    def load_sounds(self, path: str) -> None:
        """
        load all sounds from a zip file or a directory
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} doesn't exist!")

        is_zip = os.path.isfile(path)

        path = path.rstrip("/")

        if is_zip:
            soundzip = zipfile.ZipFile(path)
            files = sorted(soundzip.infolist(), key=lambda f: f.filename)
            scope = path.split(".")[0].split("/")[-1]

        else:
            files = sorted(os.listdir(path))
            scope = path.split("/")[-1]

        if self.debug >= 2:
            print_ic_style(f"loading audio scope {get_fg_color(36)}\"{scope}\"")

        for f in files:
            parts = (f.filename if is_zip else f).split(".")
            ending = parts[-1]
            filename = parts[-2]

            # only load images
            if ending.lower() not in self.filetypes:
                continue

            if self.debug >= 2:
                print_ic_style(
                    f"- texture: {get_fg_color(36)}\"{filename}\""
                )

            if is_zip:
                file = soundzip.open(f)

            else:
                file = path + "/" + f

            sound = pg.mixer.Sound(file)

            if scope not in self._sounds:
                self._sounds[scope] = {}

            self._sounds[scope][filename] = {
                "name": filename,
                "sound": sound
            }

        if self.debug:
            print_ic_style(
                f"loadinged sound scope {get_fg_color(36)}\"{scope}\""
                f"{get_fg_color(247)}"
                f", sounds: {get_fg_color(37)}{len(self._sounds[scope])}"
            )

    def get_sound(
            self,
            name: str,
            scope: str | None = None
    ) -> pg.mixer.Sound | None:
        """
        returns a sound if it exists
        """
        if scope is not None and scope not in self._sounds:
            raise ValueError(f"scope \"{scope}\" not found")

        for n_scope in self._sounds if scope is None else [scope]:
            for sound in self._sounds[n_scope]:
                # sound: NamedSound
                if self._sounds[n_scope][sound]["name"] == name:
                    if self.debug >= 3:
                        print_ic_style(
                            f"{get_fg_color(36)}\"{name}\"{get_fg_color(247)} "
                            f"found in scope {get_fg_color(36)}\"{n_scope}\""
                        )

                    return self._sounds[n_scope][sound]["sound"]

        else:
            if self.debug >= 3:
                if scope is None:
                    print_ic_style(
                        f"{get_fg_color(36)}\"{name}\"{get_fg_color(247)} "
                        f"not found in scope {get_fg_color(36)}\"{scope}\""
                    )

                else:
                    print_ic_style(
                        f"{get_fg_color(36)}\"{name}\"{get_fg_color(247)} "
                        f"not found in any loaded scope"
                    )

            return None

    def get_all_from_scope(
            self,
            scope: str,
    ) -> list[pg.mixer.Sound]:
        """
        get all textures from a scope
        """
        if scope not in self._sounds:
            raise ValueError(f"scope \"{scope}\" not found")

        if self.debug >= 2:
            print_ic_style(
                f"getting all sounds from scope {get_fg_color(36)}\"{scope}\""
            )

        out = []
        for _, sound in self._sounds[scope].items():
            if self.debug >= 3:
                print_ic_style(
                    f"- sound: {get_fg_color(36)}\"{sound["name"]}\""
                )

            out.append(sound["sound"])

        return out


sounds = _Sounds()
