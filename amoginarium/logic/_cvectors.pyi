class Vec2:
    x: float
    y: float
    xy: tuple[float, float]
    angle: float
    length: float
    polar: tuple[float, float]

    def get_length(self) -> float:
        ...

    def get_angle(self) -> float:
        ...

    def get_polar(self) -> tuple[float, float]:
        ...

    def set_length(self, length: float) -> None:
        ...

    def set_angle(self, length: float) -> None:
        ...

    def set_polar(self, angle: float, length: float) -> None:
        ...

    def dot(self, other: Vec2) -> float:
        ...

    def copy(self) -> Vec2:
        ...

    def split_vector(self, other: Vec2) -> tuple[Vec2, Vec2]:
        ...

    def normalize(self) -> Vec2:
        ...

    def mirror(self, mirror_by: Vec2) -> Vec2:
        ...

    def __add__(self, other: Vec2 | float) -> Vec2:
        ...

    def __sub__(self, other: Vec2 | float) -> Vec2:
        ...

    def __mul__(self, other: Vec2 | float) -> Vec2:
        ...

    def __truediv__(self, other: float) -> Vec2:
        ...

    def __abs__(self) -> float:
        ...

    def __repr__(self) -> str:
        ...

    def from_cartesian(self, x: float, y: float) -> Vec2:
        ...

    def from_polar(self, angle: float, length: float) -> Vec2:
        ...

