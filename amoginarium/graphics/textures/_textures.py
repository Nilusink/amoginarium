"""
_linked.py
20. March 2024

globals

Author:
Nilusink
"""

import os
import typing as tp
import zipfile

from PIL import Image

from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared.debugging import get_fg_color, print_ic_style
from amoginarium.shared.utility import convert_coord, coord_t

type mirror_t = tp.Literal["x", "y", "xy", "yx", ""]


class Texture(tp.TypedDict):
    """texture dict"""

    id: int
    name: str
    mirror: mirror_t
    size: tuple[int, int]
    pixel_perfect: tp.Optional[bool]


class FileImage(tp.TypedDict):
    """texture + file pair"""

    image: Image.Image
    name: str


class _Textures:
    _raw_images: dict[str, dict[str, FileImage]]
    _textures: dict[str, list[Texture]]
    debug: int = 1

    def __init__(self) -> None:
        self._raw_images = {}
        self._textures = {}

    def load_images(self, path: str) -> None:
        """
        load all textures from a zip file or a directory
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} doesn't exist!")

        is_zip = os.path.isfile(path)

        path = path.rstrip("/")

        img_zip = None
        if is_zip:
            img_zip = zipfile.ZipFile(path)
            files = sorted(img_zip.infolist(), key=lambda f: f.filename)
            scope = path.split(".")[0].split("/")[-1]

        else:
            files = sorted(os.listdir(path))
            scope = path.split("/")[-1]

            # filter out folders
            files = [f for f in files if os.path.isfile(os.path.join(path, f))]

        if self.debug >= 2:
            print_ic_style(f'loading texture scope {get_fg_color(36)}"{scope}"')

        for f in files:
            parts = (f.filename if is_zip else f).split(".")
            ending = parts[-1]
            filename = parts[-2]

            # only load images
            if ending.lower() not in ("png", "jpg"):
                continue

            if self.debug >= 2:
                print_ic_style(f'- texture: {get_fg_color(36)}"{filename}"')

            if img_zip:
                file = img_zip.open(f)

            else:
                file = path + "/" + f

            img = Image.open(file)

            if scope not in self._raw_images:
                self._raw_images[scope] = {}

            self._raw_images[scope][filename] = {"name": filename, "image": img}

        if self.debug:
            print_ic_style(
                f'loaded texture scope {get_fg_color(36)}"{scope}"'
                f"{get_fg_color(247)}"
                f", textures: {get_fg_color(37)}{len(self._raw_images[scope])}"
            )

    def _check_texture(
        self,
        name: str,
        mirror: str,
        size: tuple | None,
        scope: str | None = None,
        pixel_perfect: bool = False,
    ) -> Texture | None:
        """
        returns a texture if it already exists
        """
        if scope not in self._textures:
            return None

        scopes: tp.Iterable[str]
        if scope:
            scopes = [scope]

        else:
            scopes = self._raw_images.keys()

        for current_scope in scopes:
            for texture in self._textures[current_scope]:
                if texture["size"] is None:
                    is_same_size = size is None

                elif size is None:
                    is_same_size = False

                else:
                    is_same_size = set(texture["size"]) == set(size)

                if all(
                    [
                        texture["name"] == name,
                        set(texture["mirror"]) == set(mirror),
                        is_same_size,
                        texture["pixel_perfect"] == pixel_perfect,
                    ]
                ):
                    return texture

        return None

    def get_texture(
        self,
        name: str,
        size: coord_t | None = None,
        mirror: mirror_t = "",
        scope: str | None = None,
        *,
        pixel_perfect: bool = False,
    ) -> tuple[int, tuple[int, int]]:
        """
        get the ID of a texture, prevents double loading
        """
        if size is not None:
            size: tuple[float, float] = convert_coord(size)

        texture = self._check_texture(name, mirror, size, scope)

        if texture is not None:
            return texture["id"], texture["size"]

        if scope is not None:
            if scope not in self._raw_images:
                raise ValueError(f'scope "{scope}" not found')

            if name not in self._raw_images[scope]:
                raise ValueError(f'"{name}" not found in scope "{scope}"')

            _scope = scope

        else:
            for s in self._raw_images:
                if name in self._raw_images[s]:
                    if self.debug >= 3:
                        print_ic_style(
                            f'{get_fg_color(36)}"{name}"{get_fg_color(247)} '
                            f'found in scope {get_fg_color(36)}"{s}"'
                        )

                    _scope = s
                    break

            else:
                raise ValueError(f'"{name}" not found in any loaded scope')

        texture, _size = renderer.load_texture(
            image=self._raw_images[_scope][name]["image"],
            size=size,
            mirror=mirror,
            pixel_perfect=pixel_perfect,
        )

        if scope not in self._textures:
            self._textures[_scope] = []

        self._textures[_scope].append(
            {
                "id": texture,
                "mirror": mirror,
                "name": name,
                "size": _size,
                "pixel_perfect": pixel_perfect,
            }
        )

        return texture, _size

    def get_all_from_scope(
        self,
        scope: str,
        size: coord_t | None = None,
        mirror: mirror_t = "",
        pixel_perfect: bool = False,
    ) -> list[tuple[int, tuple[int, int]]]:
        """
        get all textures from a scope
        """
        if scope not in self._raw_images:
            raise ValueError(f'scope "{scope}" not found')

        if self.debug >= 2:
            print_ic_style(
                f'getting all textures from scope {get_fg_color(36)}"{scope}"'
            )

        out = []
        for _, image in self._raw_images[scope].items():
            if self.debug >= 3:
                print_ic_style(f'- texture: {get_fg_color(36)}"{image["name"]}"')

            out.append(
                self.get_texture(
                    image["name"],
                    size,
                    mirror,
                    scope=scope,
                    pixel_perfect=pixel_perfect,
                )
            )

        return out

    def get_raw_from_scope(self, scope: str) -> list[str]:
        """
        return all texture names from a scope
        """
        if scope not in self._raw_images:
            raise ValueError(f'scope "{scope}" not found')

        return list(self._raw_images[scope].keys())


textures = _Textures()
