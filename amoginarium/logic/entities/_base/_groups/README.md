# amoginarium/amoginarium/logic/entities/_base/_groups

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>


```mermaid
graph TD
    subgraph Group [" "]
        _base_group
        _entity_type_groups
        _functionality_groups
        _logic_group
        _updated
    end

    _groups --- _base_group
    _groups --- _entity_type_groups
    _groups --- _functionality_groups
    _groups --- _logic_group
    _groups --- _updated

    _base_group --> _logic_group
    _entity_type_groups --> _base_group
    _entity_type_groups --> _updated
    _functionality_groups --> _base_group
    _updated --> _base_group
```


</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>


```mermaid
graph RL
    subgraph Group1 [" "]
        BaseGroup
        LogicGroup
        _Bullets
        _FrictionXAffected
        _GravityAffected
        _Players
        _Updated
        _Walls
    end
    BaseGroup --> LogicGroup
    _Bullets --> BaseGroup
    _Players --> BaseGroup
    _Walls --> BaseGroup
    _FrictionXAffected --> BaseGroup
    _GravityAffected --> BaseGroup
    _Updated --> BaseGroup
```


</details>
