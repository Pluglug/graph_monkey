# Coding Conventions

## Naming

| Type | Pattern | Example |
|------|---------|---------|
| Operator | `SPACE_OT_addon_operation` | `GRAPH_OT_monkey_horizontally` |
| Panel | `SPACE_PT_addon_panel` | `GRAPH_PT_action_management` |
| Menu | `SPACE_MT_addon_menu` | `MONKEY_MT_transform_pie` |
| PropertyGroup | `CamelCaseSettings` | `ChannelSelectionOverlaySettings` |

## Properties

Files defining PropertyGroup, Preferences, or Operators with `bpy.props` must add at top:

```python
# pyright: reportInvalidTypeForm=false
```

This suppresses type errors for all `bpy.props` declarations in the file, so individual `# type: ignore` comments are NOT needed.

## Logging

```python
from ..utils.logging import get_logger

log = get_logger(__name__)

log.debug("Detailed info for debugging")
log.info("Normal operation info")
log.warning("Something unexpected")
log.error("Something failed")
```

## Context Checks

Always validate context in operators:

```python
@classmethod
def poll(cls, context):
    if not context.area or context.area.type != "GRAPH_EDITOR":
        return False
    if not context.space_data:
        return False
    return True
```

## Error Handling

Use `self.report()` for user-facing messages:

```python
def execute(self, context):
    if not some_condition:
        self.report({"ERROR"}, "Description of what went wrong")
        return {"CANCELLED"}

    self.report({"INFO"}, "Operation completed")
    return {"FINISHED"}
```

## Icons

Always use `ic()` wrapper for icon names to ensure version compatibility:

```python
from ..utils.ui_utils import ic

# Correct - uses version-aware wrapper
layout.label(text="Label", icon=ic("INFO"))
row.prop(self, "setting", icon=ic("PLAY"))

# Wrong - may cause errors on different Blender versions
layout.label(text="Label", icon="INFO")
```

The `ic()` function handles icon name changes between Blender versions automatically.
