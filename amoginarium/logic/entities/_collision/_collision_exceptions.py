"""
amoginarium/logic/entities/_collision/_collision_exceptions.py

Project: amoginarium
Created: 21.04.2026
Authors: LukasKrah
"""

class CollisionExceptions:
    """
    Static container for collision exception rules

    These constants are used to bypass collision checks within the collision detection system to save performance.
    NOTE: Use negative numbers, as the positives are used for root collision exceptions
          or by custom collision exception rules working with entity IDs.
    """
    GRENADE_CLUSTER_DOES_NOT_HIT_ITSELF = -10

# todo - counter function create_expcetion( -> int

# todo - wtf grenade shrep?!
