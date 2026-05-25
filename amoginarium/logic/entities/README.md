# amoginarium/amoginarium/logic/entities

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>

```mermaid
graph TD
    subgraph Group ["‎"]
        _base
        _dynamic_entities
        _items
        _player
        _spawnables
        _weaponry
        _world
    end

    entities -.- _base
    entities -.- _player
    entities -.- _spawnables
    entities -.- _weaponry
    entities -.- _world

    _dynamic_entities --> _base
    _dynamic_entities --> _weaponry
    _items --> _base
    _player --> _base
    _player --> _dynamic_entities
    _player --> _items
    _player --> _weaponry
    _spawnables --> _base
    _spawnables --> _dynamic_entities
    _spawnables --> _weaponry
    _spawnables --> _world
    _weaponry --> _base
    _weaponry --> _items
    _world --> _base
```

</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>
<!=== MermaidClassesStart ===>

```mermaid
graph RL
    subgraph Group1 ["‎"]
        CollisionType
        DetectionGroup
        EntityChildViable
        HitboxTypes
        Inventory
    end
    subgraph Group2 ["‎"]
        SensorInit
        TargetSolution
        _DetectionGroupManager
        _GameCollisions
    end
    subgraph Group3 ["‎"]
        AerodynamicEntity
        BaseChargedWeapon
        BaseLogicEntity
        BaseSensor
        BaseTurret
        BaseWeapon
        Bullet
        CollisionLogicEntity
        DebugCircleEntity
        DebugPolygonEntity
        DebugRectangleEntity
        ExactoBullet
        ExactoSniper
        ExactoTurret
        FileLoadedWeapon
        GrassIsland
        GrayBrickIsland
        GreenBrickIsland
        Grenade
        HandThrownGrenade
        HealingPotion
        Island
        Item
        JetBag
        LogicGameEntity
        MagicSensor
        Player
        PositionedLogicEntity
        RadarSensor
        RailGun
        Shield
        Something
        TargetInfo
        TextEntity
        VisualRadarSensor
        VisualSensor
        _GrenadeShrapnel
    end
    subgraph Group4 ["‎"]
        BaseGroup
        LogicGroup
        _Bullets
        _FrictionXAffected
        _GravityAffected
        _Players
        _Updated
        _Walls
    end
    PositionedLogicEntity --> BaseLogicEntity
    DebugCircleEntity --> PositionedLogicEntity
    DebugPolygonEntity --> PositionedLogicEntity
    DebugRectangleEntity --> PositionedLogicEntity
    CollisionLogicEntity --> PositionedLogicEntity
    LogicGameEntity --> CollisionLogicEntity
    BaseGroup --> LogicGroup
    _Bullets --> BaseGroup
    _Players --> BaseGroup
    _Walls --> BaseGroup
    _FrictionXAffected --> BaseGroup
    _GravityAffected --> BaseGroup
    _Updated --> BaseGroup
    HealingPotion --> Something
    Item --> LogicGameEntity
    JetBag --> Something
    Shield --> Something
    Something --> Item
    Player --> LogicGameEntity
    Grenade --> Bullet
    _GrenadeShrapnel --> Bullet
    ExactoBullet --> AerodynamicEntity
    ExactoSniper --> BaseWeapon
    ExactoTurret --> BaseTurret
    VisualRadarSensor --> VisualSensor
    VisualSensor --> LogicGameEntity
    RailGun --> BaseChargedWeapon
    HandThrownGrenade --> BaseWeapon
    AerodynamicEntity --> Bullet
    Bullet --> LogicGameEntity
    BaseSensor --> PositionedLogicEntity
    MagicSensor --> BaseSensor
    RadarSensor --> BaseSensor
    BaseTurret --> LogicGameEntity
    BaseChargedWeapon --> BaseWeapon
    BaseWeapon --> Item
    FileLoadedWeapon --> BaseWeapon
    Island --> LogicGameEntity
    GrassIsland --> Island
    GrayBrickIsland --> Island
    GreenBrickIsland --> Island
    TextEntity --> LogicGameEntity
    TargetInfo --> PositionedLogicEntity
```

<!=== MermaidClassesEnd ===>
</details>
