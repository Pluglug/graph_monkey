# Adding a New Operator

1. Create `operators/my_operator.py`
2. Follow this structure:

```python
# pyright: reportInvalidTypeForm=false
import bpy
from ..utils.logging import get_logger
from ..keymap_manager import KeymapDefinition, keymap_registry

log = get_logger(__name__)

class GRAPH_OT_my_operator(bpy.types.Operator):
    bl_idname = "graph.my_operator"
    bl_label = "My Operation"
    bl_options = {"UNDO"}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[("forward", "Forward", ""), ("backward", "Backward", "")],
        default="forward",
    )

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == "GRAPH_EDITOR"

    def execute(self, context):
        log.debug("Executing my_operator")
        # Implementation
        return {"FINISHED"}

# Keymap definitions at module level
keymap_registry.register_keymap_group("My Operator", [
    KeymapDefinition(
        operator_id="graph.my_operator",
        key="M",
        alt=True,
        properties={"direction": "forward"},
        name="Graph Editor",
        space_type="GRAPH_EDITOR",
        description="Perform my operation",
    ),
])
```

## Naming Convention

- **Operators**: `SPACE_OT_addon_operation` (e.g., `GRAPH_OT_monkey_horizontally`)
- **Panels**: `SPACE_PT_addon_panel`

## Requirements

- Always implement `poll()` classmethod
- Check `context.area.type` before accessing space-specific data
- Add `# pyright: reportInvalidTypeForm=false` at file top when using `bpy.props`
