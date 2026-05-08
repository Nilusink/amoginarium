from ._base import BaseFuze
from ._fuzes import TTLFuze, PositionFuze, ProximityFuze, TTLMultFuze, AltitudeFuze


FUZES = {
    "ttl": TTLFuze,
    "ttl_mult": TTLMultFuze,
    "distance": PositionFuze,
    "proximity": ProximityFuze,
    "alt": AltitudeFuze,
}
