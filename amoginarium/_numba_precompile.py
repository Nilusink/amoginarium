from .logic import FastVec2, point_in_triangle


def pre_compile():
    # create representative vectors
    FastVec2()
    v0 = FastVec2(0, 0)
    v1 = FastVec2(4.0, 8.0)
    v1 = FastVec2.from_polar(1, 3.2)
    v0.x, v0.y = 1.0, 2.0
    v1.x, v1.y = 3, 4

    # basic operations
    v0 + v1
    v0 - v1
    v0 * 2.0
    v0 * 2
    v0 / 2.0
    v0 / 2
    v0.dot(v1)
    v0.copy()
    v0.normalize()
    v0.set_angle(1)
    v0.set_angle(.1)
    v0.set_length(10)
    v0.set_length(1.0)
    v0.angle()
    v0.length()

    # composite functions with exactly the runtime types
    point_in_triangle(v0, v1, v0, v1)
