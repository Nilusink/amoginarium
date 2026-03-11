class Vec2:
    x: float
    y: float
    xy: tuple[float, float]
    angle: float
    length: float
    polar: tuple[float, float]

    # interaction
    def get_angle(self) -> float:
        ...

    def set_angle(self, value: float):
        ...

    def get_length(self) -> float:
        ...

    def set_length(self) -> float:
        ...

    def get_polar(self) -> tuple[float, float]:
        ...

    def set_polar(self, angle: float, length: float):
        ...

    def split_vector(self, direction):
        ...

    def dot(self, other: Vec2) -> float:
        ...

    def copy(self) -> Vec2:
        ...

    def normalize(self) -> Vec2:
        ...

    def mirror(self, mirror_by: Vec2) -> Vec2:
        ...

    # maths
    def __add__(self, other) -> Vec2:
        ...

    def __sub__(self, other) -> Vec2:
        ...

    def __mul__(self, other) -> Vec2:
        ...

    def __truediv__(self, other) -> Vec2:
        ...

    def __abs__(self):
        ...

    def __repr__(self) -> str:
        ...

    # static methods.
    # creation of new instances
    def from_cartesian(self, x, y) -> Vec2:
        ...

    def from_polar(self, angle, length) -> Vec2:
        ...


def normalize_angle(value: float) -> float:
    ...