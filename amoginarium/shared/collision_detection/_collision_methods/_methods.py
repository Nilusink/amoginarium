"""
amoginarium/shared/collision_detection/_collision_methods/_methods.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from ._aabb_aabb import AABBAABBPython, AABBAABBCython


class CollisionMethods:
    class point_point:
        ...

    # class point_circle:
    #     PointCircleCollision = PointCircleCollision

    class point_aabb:
        ...

    # class circle_point:
    #     CirclePointCollision = CirclePointCollision
    #
    # class circle_circle:
    #     CircleCircleCollision = CircleCircleCollision
    #
    # class circle_aabb:
    #     CircleAABBCollision = CircleAABBCollision

    class aabb_point:
        ...

    # class aabb_circle:
    #     AABBCircleCollision = AABBCircleCollision

    class aabb_aabb:
        Python = AABBAABBPython
        Cython = AABBAABBCython
