cimport cython
from ._cvectors cimport Vec2
from libc.stdint cimport uint8_t


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
            delta = delta.mul_double(i).div(sample_rate).add_vec2(start) # TODO: rethink logic

            try:
                if sprite.mask.get_at((delta.x, delta.y)):
                    return sprite_start.add_vec2(delta)

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
