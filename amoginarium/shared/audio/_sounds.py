"""
_sounds.py
22. March 2024

global sounds

Author:
Nilusink
"""

from amoginarium.shared.debugging import print_ic_style, get_fg_color, CC
import pygame as pg
import typing as tp
import zipfile
import json
import os


type sound_name_t = str | tuple[str, str]


class NamedSound(tp.TypedDict):
    """a sound-effect with a name"""

    sound: pg.mixer.Sound
    name: str


class _Sounds:
    _sounds: dict[str, dict[str, NamedSound]]
    _data: dict[str, dict[str, dict]]
    filetypes = ("mp3", "ogg", "wav")
    info_files = ("weights",)  # keep for processing
    debug: int = 1

    def __init__(self) -> None:
        self._sounds = {}
        self._data = {}

    def load_sounds(self, path: str) -> None:
        """
        load all sounds from a zip file or a directory
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} doesn't exist!")

        is_zip = os.path.isfile(path)

        path = path.rstrip("/")

        sound_zip: zipfile.ZipFile | None = None
        if is_zip:
            sound_zip: zipfile.ZipFile = zipfile.ZipFile(path)
            files = sorted(sound_zip.infolist(), key=lambda file: file.filename)
            scope = path.split(".")[0].split("/")[-1]

        else:
            files = sorted(
                file
                for file in os.listdir(path)
                if os.path.isfile(os.path.join(path, file))
            )
            scope = path.split("/")[-1]

        if self.debug >= 2:
            print_ic_style(f'loading audio scope {get_fg_color(36)}"{scope}"')

        for f in files:
            parts = (f.filename if is_zip else f).split(".")
            ending = parts[-1]
            filename = parts[-2]

            # check if file type in info files
            if ending.lower() in self.info_files:
                if scope not in self._data:
                    self._data[scope] = {}

                if sound_zip:
                    fp = sound_zip.open(f)

                else:
                    fp = open(path + "/" + f)

                # append to data scope
                try:
                    self._data[scope][ending.lower()] = json.load(fp)

                except json.JSONDecodeError:
                    print_ic_style(
                        f"{CC.fg.RED}- invalid info json: "
                        f"{CC.fg.YELLOW}{scope}::{ending}"
                    )

                continue

            # only load images
            if ending.lower() not in self.filetypes:
                continue

            if self.debug >= 2:
                print_ic_style(f'- texture: {get_fg_color(36)}"{filename}"')

            if sound_zip:
                file = sound_zip.open(f)

            else:
                file = path + "/" + f

            sound = pg.mixer.Sound(file)

            if scope not in self._sounds:
                self._sounds[scope] = {}

            self._sounds[scope][filename] = {"name": filename, "sound": sound}

        if self.debug:
            print_ic_style(
                f'loaded sound scope {get_fg_color(36)}"{scope}"'
                f"{get_fg_color(247)}"
                f", sounds: {get_fg_color(37)}{len(self._sounds[scope])}"
            )

    def get_sound(self, name: str, scope: str | None = None) -> pg.mixer.Sound | None:
        """
        returns a sound if it exists
        """
        if scope is not None and scope not in self._sounds:
            raise ValueError(f'scope "{scope}" not found')

        for n_scope in self._sounds if scope is None else [scope]:
            for sound in self._sounds[n_scope]:
                # sound: NamedSound
                if self._sounds[n_scope][sound]["name"] == name:
                    if self.debug >= 3:
                        print_ic_style(
                            f'{get_fg_color(36)}"{name}"{get_fg_color(247)} '
                            f'found in scope {get_fg_color(36)}"{n_scope}"'
                        )

                    return self._sounds[n_scope][sound]["sound"]

        else:
            if self.debug >= 3:
                if scope is None:
                    print_ic_style(
                        f'{get_fg_color(36)}"{name}"{get_fg_color(247)} '
                        f'not found in scope {get_fg_color(36)}"{scope}"'
                    )

                else:
                    print_ic_style(
                        f'{get_fg_color(36)}"{name}"{get_fg_color(247)} '
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
            raise ValueError(f'scope "{scope}" not found')

        if self.debug >= 2:
            print_ic_style(f'getting all sounds from scope {get_fg_color(36)}"{scope}"')

        out = []
        for _, sound in self._sounds[scope].items():
            if self.debug >= 3:
                print_ic_style(f'- sound: {get_fg_color(36)}"{sound["name"]}"')

            out.append(sound["sound"])

        return out

    def get_scope_info(self, scope: str) -> dict[str, dict]:
        """
        get info dicts from loaded scope

        :returns: info dict (empty if not loaded)
        """
        if scope not in self._data:
            return {}

        return self._data[scope]


sounds = _Sounds()
