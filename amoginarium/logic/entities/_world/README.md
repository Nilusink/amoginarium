# amoginarium/amoginarium/logic/entities/_world

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>
<!--- MermaidStructureStart --->

```mermaid
graph TD
    subgraph Group ["‎"]
        _base_island
        _islands
        _text_entity
    end

    _world --- _base_island
    _world --- _islands
    _world --- _text_entity

    _islands --> _base_island
```

<!--- MermaidStructureEnd --->
</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>
<!--- MermaidClassesStart --->

```mermaid
graph RL
    subgraph Group1 ["‎"]
        TextEntity
    end
    subgraph Group2 ["‎"]
        GrassIsland
        GrayBrickIsland
        GreenBrickIsland
        Island
    end
    GrassIsland --> Island
    GrayBrickIsland --> Island
    GreenBrickIsland --> Island
```

<!--- MermaidClassesEnd --->
</details>
