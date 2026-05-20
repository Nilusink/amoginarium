# amoginarium/amoginarium/logic/entities/_items

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>

<!--- MermaidStructureStart --->

```mermaid
graph TD
    subgraph Group ["‎"]
        _healing_potion
        _inventory
        _item
        _jet_bag
        _shield
        _something
    end

    _items --- _healing_potion
    _items --- _inventory
    _items --- _item
    _items --- _jet_bag
    _items --- _shield
    _items --- _something

    _healing_potion --> _something
    _inventory --> _item
    _jet_bag --> _something
    _shield --> _something
    _something --> _item
```

<!--- MermaidStructureEnd --->

</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>

<!--- MermaidClassesStart --->

```mermaid
graph RL
    subgraph Group1 ["‎"]
        Inventory
    end
    subgraph Group2 ["‎"]
        HealingPotion
        Item
        JetBag
        Shield
        Something
    end
    HealingPotion --> Something
    JetBag --> Something
    Shield --> Something
    Something --> Item
```

<!--- MermaidClassesEnd --->

</details>
