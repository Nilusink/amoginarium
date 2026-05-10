# amoginarium/amoginarium/logic/entities/_base/_collision

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>
<!--- MermaidStructureStart --->

```mermaid
graph TD
    subgraph Group ["‎"]
        _game_collisions
        _collision_types
    end

    _collision --- _game_collisions
    _collision --- _collision_types

    _game_collisions --> _collision_types
```

<!--- MermaidStructureEnd --->
</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>
<!--- MermaidClassesStart --->

```mermaid
graph RL
    subgraph Group1 ["‎"]
        CollisionType
        HitboxTypes
        _GameCollisions
    end
```

<!--- MermaidClassesEnd --->
</details>
