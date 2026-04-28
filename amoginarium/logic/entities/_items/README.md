# amoginarium/amoginarium/logic/entities/_items

<details open>

<summary><h2 style="display:inline-block">Structure</h2></summary>

<!--- MermaidStructureStart --->
```mermaid
graph TD
    subgraph Group [" "]
        _base_item
        _healing_potion
        _inventory
        _item
        _jet_bag
        _shield
    end

    _items --- _base_item
    _items --- _healing_potion
    _items --- _inventory
    _items --- _item
    _items --- _jet_bag
    _items --- _shield

    _base_item --> _item
    _healing_potion --> _base_item
    _inventory --> _item
    _jet_bag --> _base_item
    _shield --> _base_item
```
<!--- MermaidStructureEnd --->

</details>

<details open>

<summary><h2 style="display:inline-block">Classes</h2></summary>

<!--- MermaidClassesStart --->
```mermaid
graph RL
    subgraph Group1 [" "]
        Inventory
    end
    subgraph Group2 [" "]
        BaseItem
        HealingPotion
        Item
        JetBag
        Shield
    end
    BaseItem --> Item
    HealingPotion --> BaseItem
    JetBag --> BaseItem
    Shield --> BaseItem
```
<!--- MermaidClassesEnd --->

</details>
