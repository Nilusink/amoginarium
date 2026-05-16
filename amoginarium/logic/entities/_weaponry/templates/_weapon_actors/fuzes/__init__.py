from ._fuzes import TTLFuze, PositionFuze, ProximityFuze, TTLMultFuze, AltitudeFuze
from ._base import BaseFuze


FUZES: dict[str, type[BaseFuze]] = {
    "ttl": TTLFuze,
    "ttl_mult": TTLMultFuze,
    "distance": PositionFuze,
    "proximity": ProximityFuze,
    "alt": AltitudeFuze,
}
