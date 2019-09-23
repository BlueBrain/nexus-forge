from typing import Tuple


def sort_attributes(x: Tuple[str, str]) -> Tuple[int, str]:
    # POLICY Should be called to sort attributes of resources, templates, mappings, ...
    ordered = ["_last_action", "_validated", "_synchronized", "_store_metadata", "type", "id"]
    orders = {x: i for i, x in enumerate(ordered)}
    next_order = len(ordered) + 1
    return orders.get(x[0], next_order)
