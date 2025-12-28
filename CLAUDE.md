# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**MonKey** (Graph Monkey) is a Blender animation addon that enhances Graph Editor workflow with keyframe manipulation tools, playback controls, and pose visualization. Version 0.9.0, supports Blender 2.80+ (some features require 4.4+).

## Architecture

### Module Loading System (addon.py)

The addon uses an **automatic dependency-resolving module loader**:

1. **Pattern-based discovery**: Modules matching patterns in `__init__.py` are collected
2. **AST-based dependency analysis**: Import statements are parsed to detect dependencies
3. **Topological sorting**: Kahn's algorithm determines load order
4. **Automatic class registration**: All `bpy.types.bpy_struct` subclasses are registered in dependency order

```python
# __init__.py configures which modules to load
addon.init_addon(
    module_patterns=[
        "constants",
        "preferences",
        "keymap_manager",
        "operators.*",
        "ui.*",
        "utils.*",
    ],
    use_reload=use_reload,
)
```

### Adding a New Operator

1. Create `operators/my_operator.py`
2. Follow this structure:

```python
import bpy
from ..utils.logging import get_logger
from ..keymap_manager import KeymapDefinition, keymap_registry

log = get_logger(__name__)

class GRAPH_OT_my_operator(bpy.types.Operator):
    bl_idname = "graph.my_operator"
    bl_label = "My Operation"
    bl_options = {"UNDO"}

    # Properties with type: ignore for bpy.props
    direction: bpy.props.EnumProperty(  # type: ignore
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

**No manual registration needed** - the framework handles class registration automatically.

### Adding Settings/Preferences

1. Create a `PropertyGroup` in your module:

```python
class MyOperatorSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(default=True)

    def draw(self, context, layout):
        layout.prop(self, "enabled")
```

2. Add `PointerProperty` to `MonKeyPreferences` in `preferences.py`:

```python
from .operators.my_operator import MyOperatorSettings

class MonKeyPreferences(AddonPreferences):
    my_settings: PointerProperty(type=MyOperatorSettings)
```

3. Access via `addon.get_prefs(context).my_settings`

### Keymap System (keymap_manager.py)

Declarative keymap registration using `KeymapDefinition` dataclass:

```python
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
)
```

Register groups with `keymap_registry.register_keymap_group("Group Name", [...])`

### Key Utilities

- **`addon.get_prefs(context)`**: Get addon preferences
- **`get_logger(__name__)`**: Create module logger (from `utils.logging`)
- **`ic(icon_name)`**: Icon with version fallback (from `utils.ui_utils`)
- **`get_visible_fcurves(context)`**: Safely retrieve visible F-curves (from `operators.dopesheet_helper`)

### Reusable Utility Modules

#### utils/config_props.py - Blender Config Property System
A framework for creating BoolProperties that sync with Blender's internal settings:

```python
from ..utils.config_props import BlenderConfigProperty

def get_my_state():
    return bpy.context.space_data.some_setting

def set_my_state(enabled):
    bpy.context.space_data.some_setting = enabled

MY_CONFIG = BlenderConfigProperty(
    name="My Setting",
    description="Description",
    get_func=get_my_state,
    set_func=set_my_state,
    cache_enabled=True,    # LRU cache for performance
    async_update=False,    # Use True for heavy operations
)

class MySettings(PropertyGroup):
    my_setting: MY_CONFIG.create_property()
```

Features: intelligent caching (`PerformanceCache`), async updates via timer, profiling (`ConfigProfiler`).

#### utils/timer.py - Delayed Execution
```python
from ..utils.timer import timeout, Timer

# Execute function asynchronously (next frame)
timeout(my_function, arg1, arg2)

# Manual timer for animations/fades
timer = Timer(duration=1.0)
timer.elapsed_ratio()  # 0.0 → 1.0
timer.is_finished()
```

#### utils/overlay_utils.py - Viewport Text Drawing
```python
from ..utils.overlay_utils import TextPainter, calculate_aligned_position

# Text with shadow and fade-out
painter = TextPainter(
    text="Status",
    size=24,
    color=(1.0, 1.0, 1.0, 1.0),
    shadow=True,
    timer_duration=2.0,
)
painter.draw(x, y)

# Alignment calculation
x, y = calculate_aligned_position(
    alignment="TOP_RIGHT",  # TOP_LEFT, CENTER, BOTTOM_RIGHT, etc.
    space_width, space_height,
    object_width, object_height,
    offset_x=10, offset_y=10,
)
```

#### utils/anim_utils.py - Animation Frame Utilities
```python
from ..utils.anim_utils import (
    collect_allowed_frames_in_range,
    get_allowed_frames_in_range_cached,
    select_target_frame_from_list,
    find_timeline_area,
)

# Get keyframe frames with TTL cache
frames = get_allowed_frames_in_range_cached(
    context, start_frame=1, end_frame=250,
    allowed_types={"KEYFRAME", "BREAKDOWN"},
    ttl_seconds=0.1,
)

# Find next/previous frame
target = select_target_frame_from_list(frames, current=50, go_next=True, allow_loop=True)
```

#### utils/bone_transform_utils.py - Pose Bone Analysis
```python
from ..utils.bone_transform_utils import (
    get_bone_transform_difference,
    get_bone_axes_world,
    magnitude_to_color,
    BoneTransformDifference,
)

# Get local transform difference from rest pose
diff: BoneTransformDifference = get_bone_transform_difference(pose_bone)
diff.rotation_angle_deg    # Rotation in degrees
diff.location_magnitude    # Translation distance
diff.has_any_change        # Quick check

# Get bone axes in world space
origin, x_axis, y_axis, z_axis = get_bone_axes_world(pose_bone, rest_pose=False)

# Heatmap color from value
rgb = magnitude_to_color(angle, min_value=0, max_value=180, color_scheme="heat")
```

### Directory Structure

```
MonKey/
├── __init__.py          # bl_info and module pattern config
├── addon.py             # Module loading framework
├── keymap_manager.py    # Keymap registration system
├── constants.py         # Shared type definitions
├── preferences.py       # AddonPreferences with nested settings
├── operators/           # Operator modules (auto-discovered)
├── ui/                  # Panels and UI elements
│   └── pies/            # Pie menus
└── utils/               # Shared utilities
```

## Conventions

### Naming
- **Operators**: `SPACE_OT_addon_operation` (e.g., `GRAPH_OT_monkey_horizontally`)
- **Panels**: `SPACE_PT_addon_panel`
- **PropertyGroups**: `CamelCaseSettings`

### Properties
- **Files defining PropertyGroup or Preferences** must add at the top:
  ```python
  # pyright: reportInvalidTypeForm=false
  ```
- Always add `# type: ignore` to individual bpy.props declarations
- Include description in property definition

### Logging
- Use `log = get_logger(__name__)` at module level
- Levels: `log.debug()`, `log.info()`, `log.warning()`, `log.error()`

### Context Checks
- Always implement `poll()` classmethod for operators
- Check `context.area.type` before accessing space-specific data

### Dependencies
- For non-obvious dependencies, add module-level `DEPENDS_ON` list:
  ```python
  DEPENDS_ON = ["utils.some_utility"]
  ```
- Use `TYPE_CHECKING` for import-only type hints to avoid circular imports

## Language

Comments and documentation in this codebase use both Japanese and English. Either is acceptable for new additions.
