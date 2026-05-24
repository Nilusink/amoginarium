"""
Radar track.

Track type where track is updated by position + velocity

Path: amoginarium/shared/utility/_tracks/_cradar_track.pyx
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from ._base_track cimport BaseTrack
from ._base_track import TrackQuality


cdef class RadarTrack2D(BaseTrack):
    """
    Radar track.

    Track type where track is updated by position + velocity
    """

    def __cinit__(
        self,
        double measurement_noise_pos=0.0,
        double measurement_noise_vel=0.0,
    ):
        self.measurement_noise_pos = measurement_noise_pos
        self.measurement_noise_vel = measurement_noise_vel

        self.reset()

    cpdef reset(self):
        self.x = 0
        self.y = 0

        self.vx = 0
        self.vy = 0

        self.ax = 0
        self.ay = 0

        self.px = 1000
        self.py = 1000

        self.pvx = 1000
        self.pvy = 1000

        self.prev_vx = 0
        self.prev_vy = 0

    cpdef initialize(self, double x, double y, double vx, double vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.prev_vx = vx
        self.prev_vy = vy

        BaseTrack.initialize(self, x, y, vx, vy)
        self._track_quality = TrackQuality.POS_AND_VEL.value

    cdef predict(self, double dt):
        if dt == 0:
            return

        self.x += self.vx * dt
        self.y += self.vy * dt

        # # optional gravity / accel model
        self.vx += self.ax * dt
        self.vy += self.ay * dt


    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        cdef:
            double target_ax, target_ay
            double last_update_dt = self.last_update
        # position
        # cdef double kx = self.px / (self.px + self.measurement_noise_pos)
        # cdef double ky = self.py / (self.py + self.measurement_noise_pos)
        #
        # self.x += kx * (mx - self.x)
        # self.y += ky * (my - self.y)

        if dt == 0:
            return

        BaseTrack.update(self, mx, my, mvx, mvy, dt)

        self.x = mx
        self.y = my

        # velocity
        self.vx = mvx
        self.vy = mvy

        # cdef double kvx = self.pvx / (self.pvx + self.measurement_noise_vel)
        # cdef double kvy = self.pvy / (self.pvy + self.measurement_noise_vel)
        #
        # self.vx += kvx * (mvx - self.vx)
        # self.vy += kvy * (mvy - self.vy)

        # acceleration
        self.ax = (self.vx - self.prev_vx) / last_update_dt
        self.ay = (self.vy - self.prev_vy) / last_update_dt

        # self.ax *= 0.99
        # self.ay *= 0.99

        # self.ax += 0.1 * (mvx - self.prev_vx) / dt
        # self.ay += 0.1 * (mvy - self.prev_vy) / dt

        # target_ax = (mvx - self.prev_vx) / last_update_dt
        # target_ay = (mvy - self.prev_vy) / last_update_dt
        #
        # self.ax += (target_ax - self.ax) * 0.5
        # self.ay += (target_ay - self.ay) * 0.5

        # prev values
        self.prev_vx = self.vx
        self.prev_vy = self.vy

        self._track_quality = TrackQuality.POS_VEL_ACC.value
