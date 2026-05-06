# amoginarium/amoginarium/logic/entities/_base/_base_entities

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>
<!--- MermaidStructureStart --->

```mermaid
graph TD
    subgraph Group ["‎"]
        _base_logic_entity
        _positioned_logic_entity
    end

    _base_entities --- _base_logic_entity
    _base_entities --- _positioned_logic_entity

    _positioned_logic_entity --> _base_logic_entity
```

<!--- MermaidStructureEnd --->
</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>
<!--- MermaidClassesStart --->

```mermaid
graph RL
    subgraph Group1 ["‎"]
        EntityChildViable
    end
    subgraph Group2 ["‎"]
        BaseLogicEntity
        PositionedLogicEntity
    end
    PositionedLogicEntity --> BaseLogicEntity
```

<!--- MermaidClassesEnd --->
</details>
