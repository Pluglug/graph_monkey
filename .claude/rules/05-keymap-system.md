# Keymap System

Declarative keymap registration using `KeymapDefinition` dataclass in `keymap_manager.py`.

## Basic Usage

```python
from ..keymap_manager import KeymapDefinition, keymap_registry

keymap_registry.register_keymap_group("My Feature", [
    KeymapDefinition(
        operator_id="graph.my_operator",
        key="A",                    # Key identifier
        value="PRESS",              # PRESS, RELEASE, CLICK, etc.
        shift=0, ctrl=0, alt=1,     # Modifiers (0=don't care, 1=required)
        space_type="GRAPH_EDITOR",  # Context space type
        region_type="WINDOW",
        properties={"param": "value"},
        description="What this does",
        repeat=True,                # Allow key repeat
    ),
])
```

## KeymapDefinition Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `operator_id` | str | required | e.g., `"graph.my_operator"` |
| `key` | str | required | Key identifier (e.g., `"A"`, `"F1"`, `"LEFTMOUSE"`) |
| `value` | str | `"PRESS"` | Event type |
| `shift/ctrl/alt/oskey` | int | `0` | Modifier state |
| `space_type` | str | `"VIEW_3D"` | Context space |
| `name` | str | `"3D View"` | Keymap name for UI |
| `properties` | dict | `{}` | Operator properties |
| `repeat` | bool | `False` | Allow key repeat |
| `active` | bool | `True` | Enable/disable |

## Multiple Keymaps for One Operator

```python
keymap_registry.register_keymap_group("Direction Keys", [
    KeymapDefinition(
        operator_id="graph.move",
        key="W", alt=True,
        properties={"direction": "up"},
    ),
    KeymapDefinition(
        operator_id="graph.move",
        key="S", alt=True,
        properties={"direction": "down"},
    ),
])
```
