from ._base import BaseFuze
from ._fuzes import AltitudeFuze, PositionFuze, ProximityFuze, TTLFuze, TTLMultFuze

FUZES: dict[str, type[BaseFuze]] = {
    "ttl": TTLFuze,
    "ttl_mult": TTLMultFuze,
    "distance": PositionFuze,
    "proximity": ProximityFuze,
    "alt": AltitudeFuze,
}
