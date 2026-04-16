"""
amoginarium/shared/collision_detection/_collision_methods/_collision_method.py
"""

class CollisionMethod:
    @staticmethod
    def collision[T1, T2](
            group_a, group_b,
            entities_a, entities_b, grid_b,
            a_px_o, a_py_o, a_px_n, a_py_n, a_sx, a_sy,
            b_px_o, b_py_o, b_px_n, b_py_n, b_sx, b_sy,
            callback_a, callback_b
    ) -> None:
        ...