"""
_linked.py
20. March 2024

globals

Author:
Nilusink
"""
from ..debugging import print_ic_style, get_fg_color
from ..logic import coord_t, convert_coord
from ..render_bindings import renderer
from PIL import Image
import typing as tp
import zipfile
import os


type mirror_t = tp.Literal["x", "y", "xy", "yx"]


class Texture(tp.TypedDict):
    name: str
    size: tuple[int, int]
    mirror: mirror_t
    id: int


class FileImage(tp.TypedDict):
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

        if is_zip:
            imgzip = zipfile.ZipFile(path)
            files = sorted(imgzip.infolist(), key=lambda f: f.filename)
            scope = path.split(".")[0].split("/")[-1]

        else:
            files = sorted(os.listdir(path))
            scope = path.split("/")[-1]

            # filter out folders
            files = [f for f in files if os.path.isfile(os.path.join(path, f))]

        if self.debug >= 2:
            print_ic_style(f"loading texture scope "
                           f"{get_fg_color(36)}\"{scope}\"")

        for f in files:
            parts = (f.filename if is_zip else f).split(".")
            ending = parts[-1]
            filename = parts[-2]

            # only load images
            if ending.lower() not in ("png", "jpg"):
                continue

            if self.debug >= 2:
                print_ic_style(
                    f"- texture: {get_fg_color(36)}\"{filename}\""
                )

            if is_zip:
                file = imgzip.open(f)

            else:
                file = path + "/" + f

            img = Image.open(file)

            if scope not in self._raw_images:
                self._raw_images[scope] = {}

            self._raw_images[scope][filename] = {
                "name": filename,
                "image": img
            }

        if self.debug:
            print_ic_style(
                f"loadinged texture scope {get_fg_color(36)}\"{scope}\""
                f"{get_fg_color(247)}"
                f", textures: {get_fg_color(37)}{len(self._raw_images[scope])}"
            )

    def _check_texture(
            self,
            name: str,
            mirror: str,
            size: tuple | None,
            scope: str | None = None
    ) -> Texture | None:
        """
        returns a texture if it already exists
        """
        if scope not in self._textures:
            return None

        for scope in self._raw_images if scope is None else [scope]:
            for texture in self._textures[scope]:
                if texture["size"] is None:
                    is_same_size = size is None

                elif size is None:
                    is_same_size = False

                else:
                    is_same_size = set(texture["size"]) == set(size)

                if all([
                    texture["name"] == name,
                    set(texture["mirror"]) == set(mirror),
                    is_same_size
                ]):
                    return Texture

        return None

    def get_texture(
            self,
            name: str,
            size: coord_t | None = None,
            mirror: mirror_t = "",
            scope: str | None = None
    ) -> tuple[int, tuple[int, int]]:
        """
        get the ID of a texture, prevents double loading
        """
        if size is not None:
            size = convert_coord(size)

        texture = self._check_texture(name, mirror, size, scope)

        if texture is not None:
            return texture["id"], texture["size"]

        if scope is not None:
            if scope not in self._raw_images:
                raise ValueError(f"scope \"{scope}\" not found")

            if name not in self._raw_images[scope]:
                raise ValueError(f"\"{name}\" not found in scope \"{scope}\"")

        else:
            for s in self._raw_images:
                if name in self._raw_images[s]:
                    if self.debug >= 3:
                        print_ic_style(
                            f"{get_fg_color(36)}\"{name}\"{get_fg_color(247)} "
                            f"found in scope {get_fg_color(36)}\"{s}\""
                        )

                    scope = s
                    break

            else:
                raise ValueError(f"\"{name}\" not found in any loaded scope")

        texture, size = renderer.load_texture(
            image=self._raw_images[scope][name]["image"],
            size=size,
            mirror=mirror
        )

        if scope not in self._textures:
            self._textures[scope] = []

        self._textures[scope].append({
            "id": texture,
            "mirror": mirror,
            "name": name,
            "size": size
        })

        return texture, size

    def get_all_from_scope(
            self,
            scope: str,
            size: coord_t | None = None,
            mirror: str = "",
    ) -> list[tuple[int, tuple[int, int]]]:
        """
        get all textures from a scope
        """
        if scope not in self._raw_images:
            raise ValueError(f"scope \"{scope}\" not found")

        if self.debug >= 2:
            print_ic_style(
                f"getting all textures from scope {get_fg_color(36)}\"{scope}\""
            )

        out = []
        for _, image in self._raw_images[scope].items():
            if self.debug >= 3:
                print_ic_style(
                    f"- texture: {get_fg_color(36)}\"{image["name"]}\""
                )

            out.append(self.get_texture(
                image["name"],
                size,
                mirror,
                scope=scope
            ))

        return out

    def get_raw_from_scope(self, scope: str) -> list[str]:
        """
        return all texture names from a scope
        """
        if scope not in self._raw_images:
            raise ValueError(f"scope \"{scope}\" not found")

        return list(self._raw_images[scope].keys())


textures = _Textures()
