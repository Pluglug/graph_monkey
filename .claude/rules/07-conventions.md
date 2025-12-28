# Coding Conventions

## Naming

| Type | Pattern | Example |
|------|---------|---------|
| Operator | `SPACE_OT_addon_operation` | `GRAPH_OT_monkey_horizontally` |
| Panel | `SPACE_PT_addon_panel` | `GRAPH_PT_action_management` |
| Menu | `SPACE_MT_addon_menu` | `MONKEY_MT_transform_pie` |
| PropertyGroup | `CamelCaseSettings` | `ChannelSelectionOverlaySettings` |

## Properties

Files defining PropertyGroup or Preferences must add at top:

```python
# pyright: reportInvalidTypeForm=false
```

Individual properties need type ignore:

```python
enabled: bpy.props.BoolProperty(default=True)  # type: ignore
```

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
