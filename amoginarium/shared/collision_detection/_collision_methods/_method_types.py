"""
amoginarium/shared/collision_detection/_collision_methods/_types.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from ._base_method import CollisionMethod


# region Point collision methods
class PointPointCollision(CollisionMethod):
    ...

# class PointCircleCollision(CollisionMethod):
#     ...

class PointAABBCollision(CollisionMethod):
    ...

# endregion

# region Circle collision methods
# CirclePointCollision = PointCircleCollision

# class CircleCircleCollision(CollisionMethod):
#     ...
#
# class CircleAABBCollision(CollisionMethod):
#     ...

# endregion

# region AABB collision methods
AABBPointCollision = PointAABBCollision
# AABBCircleCollision = CircleAABBCollision

class AABBAABBCollision(CollisionMethod):
    ...

# endregion