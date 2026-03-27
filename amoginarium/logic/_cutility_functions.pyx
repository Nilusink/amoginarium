# cython: boundscheck=False, wraparound=False, cdivision=True
cimport cython
from ._cvectors cimport Vec2
from libc.stdint cimport uint8_t


cpdef object convert_coord(object coord, object convert_to = tuple):
    if convert_to is Vec2:
        if isinstance(coord, Vec2):
            return (<Vec2>coord).copy()
        return Vec2().from_cartesian(coord[0], coord[1])

    elif convert_to is tuple:
        if isinstance(coord, tuple):
            return coord
        return (<Vec2>coord).xy

    elif convert_to is int:
        if isinstance(coord, Vec2):
            coord = (<Vec2>coord).xy
        return int(coord[0]), int(coord[1])

    else:
        raise ValueError("Unsupported conversion:", convert_to)


cpdef bint is_related(object a, object b, int depth=2):
    cdef bint is_same
    cdef object a_parent, b_parent
    cdef object a_coal, b_coal

    # depth 1
    is_same = (a == b)
    if depth <= 1:
        return is_same

    elif is_same:
        return True

    # fetch parents once (no exceptions)
    a_parent = getattr(a, "parent", None)
    b_parent = getattr(b, "parent", None)

    # parent relation
    if a_parent is b or b_parent is a:
        if depth <= 2:
            return True
    elif depth <= 2:
        return is_same

    # sibling check
    if depth <= 3:
        if a_parent is not None and b_parent is not None:
            if a_parent == b_parent:
                return True
        return is_same or (a_parent is b or b_parent is a)

    # coalition check
    a_coal = getattr(a, "coalition", None)
    b_coal = getattr(b, "coalition", None)

    if depth <= 4:
        if a_coal is not None and a_coal == b_coal:
            return True

        return (
            is_same or
            (a_parent is b or b_parent is a) or
            (a_parent is not None and a_parent == b_parent)
        )

    return False


cpdef Vec2 raycast_mask(
        object sprite,
        Vec2 start,
        Vec2 end,
        uint8_t sample_rate = 10
):
    # subtract sprites position (masks don't have positions)
    cdef Vec2 sprite_start = sprite.position

    # check if in collision box first to save time
    clipped = sprite.rect.clipline((start.x, start.y), (end.x, end.y))
    cdef Vec2 delta
    if clipped:
        # only calculate points actually in sprite
        # start, end = clipped

        # position offsets
        start = Vec2().from_cartesian(clipped[0][0], clipped[0][1]).sub_vec2(sprite_start)
        end = Vec2().from_cartesian(clipped[1][0], clipped[1][1]).sub_vec2(sprite_start)

        # calculate line
        delta = end.sub_vec2(start)
        sample_rate = int(
            max(abs(delta.x), abs(delta.y)) / sample_rate
        )

        # trace line through entity
        for i in range(sample_rate):
            d = delta.mul_double(i).div(sample_rate).add_vec2(start)

            try:
                if sprite.mask.get_at((d.x, d.y)):
                    return sprite_start.add_vec2(d)

            except IndexError:
                continue

    return Vec2()


cpdef bint point_in_triangle(
        Vec2 p,
        Vec2 a,
        Vec2 b,
        Vec2 c
):
    """
    p: point to test
    a,b,c: triangle vertices
    """
    cdef Vec2 v0 = c.sub_vec2(a)
    cdef Vec2 v1 = b.sub_vec2(a)
    cdef Vec2 v2 = p.sub_vec2(a)

    cdef double dot00 = v0.dot(v0)
    cdef double dot01 = v0.dot(v1)
    cdef double dot02 = v0.dot(v2)
    cdef double dot11 = v1.dot(v1)
    cdef double dot12 = v1.dot(v2)

    cdef double denom = dot00 * dot11 - dot01 * dot01
    if denom == 0:
        return False

    cdef double inv = 1 / denom
    cdef double u = (dot11 * dot02 - dot01 * dot12) * inv
    cdef double v = (dot00 * dot12 - dot01 * dot02) * inv

    return (u >= 0) and (v >= 0) and (u + v <= 1)


cpdef bint infinite_lines_intersect(Vec2 a, Vec2 b, Vec2 c, Vec2 d):
    cdef double denom = (b.x - a.x)*(d.y - c.y) - (b.y - a.y)*(d.x - c.x)
    return denom != 0  # not parallel


cpdef Vec2 raycast_size(Vec2 a, Vec2 b, Vec2 center, double radius):
    cdef Vec2 d = b.sub_vec2(a)  # direction: b - a
    cdef Vec2 f = a.sub_vec2(center)  # from center to start

    cdef double A = d.dot(d)
    cdef double B = 2.0 * f.dot(d)
    cdef double C = f.dot(f) - radius * radius

    if A == 0.0:
        return None

    cdef double discriminant = B * B - 4.0 * A * C
    cdef double sqrt_disc, t1, t2

    if discriminant < 0.0:
        return None  # no hit

    sqrt_disc = discriminant ** 0.5

    # nearer intersection first
    t1 = (-B - sqrt_disc) / (2.0 * A)
    if 0.0 <= t1 <= 1.0:
        return a.add_vec2(d.mul_double(t1))

    t2 = (-B + sqrt_disc) / (2.0 * A)
    if 0.0 <= t2 <= 1.0:
        return a.add_vec2(d.mul_double(t2))

    return None
