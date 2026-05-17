"""
amoginarium/graphics/ui/_animations/_curves.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""


class PeakedSCurve:
    """Peaked S-Curve"""

    JUMP_VAL = 0.10
    JUMP_END_TIME = 0.05

    PEAK_VAL = 1.25
    PEAK_TIME = 0.8

    END_VAL = 1.0

    @classmethod
    def peaked_s_curve(cls, x: float) -> float:
        """
        Returns the value of the Peaked S-Curve at time x.
        :param x: Relative time from 0 to 1
        :return: Calculated value
        """
        x = max(0.0, min(1.0, x))

        # 1. The Initial Jump
        if x < cls.JUMP_END_TIME:
            return cls.JUMP_VAL

        # 2. Scaling from Jump to Peak
        if x <= cls.PEAK_TIME:
            # Normalize x from [JUMP_END_TIME, PEAK_TIME] to [0.0, 1.0]
            t = (x - cls.JUMP_END_TIME) / (cls.PEAK_TIME - cls.JUMP_END_TIME)
            # Smoothstep (Cubic Hermite)
            smooth = t**2 * (3 - 2 * t)
            return cls.JUMP_VAL + (cls.PEAK_VAL - cls.JUMP_VAL) * smooth

        # 3. Settling from Peak to End
        else:
            # Normalize x from [PEAK_TIME, 1.0] to [0.0, 1.0]
            t = (x - cls.PEAK_TIME) / (1.0 - cls.PEAK_TIME)
            # Smoothstep
            smooth = t**2 * (3 - 2 * t)
            return cls.PEAK_VAL - (cls.PEAK_VAL - cls.END_VAL) * smooth


peaked_s_curve = PeakedSCurve.peaked_s_curve
