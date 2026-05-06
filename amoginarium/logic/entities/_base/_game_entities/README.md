# amoginarium/amoginarium/logic/entities/_base/_game_entities

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>
<!--- MermaidStructureStart --->

```mermaid
graph TD
    subgraph Group ["‎"]
        _collision_logic_entity
        _logic_game_entity
    end

    _game_entities --- _collision_logic_entity
    _game_entities --- _logic_game_entity

    _logic_game_entity --> _collision_logic_entity
```

<!--- MermaidStructureEnd --->
</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>
<!--- MermaidClassesStart --->

```mermaid
graph RL
    subgraph Group1 ["‎"]
        CollisionLogicEntity
        LogicGameEntity
    end
    LogicGameEntity --> CollisionLogicEntity
```

<!--- MermaidClassesEnd --->
</details>
