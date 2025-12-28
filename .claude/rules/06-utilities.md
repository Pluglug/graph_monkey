# Reusable Utility Modules

## utils/config_props.py - Blender Config Property System

Framework for BoolProperties that sync with Blender's internal settings:

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

Features: `PerformanceCache`, async updates via timer, `ConfigProfiler`.

## utils/timer.py - Delayed Execution

```python
from ..utils.timer import timeout, Timer

# Execute function asynchronously (next frame)
timeout(my_function, arg1, arg2)

# Manual timer for animations/fades
timer = Timer(duration=1.0)
timer.elapsed_ratio()  # 0.0 → 1.0
timer.is_finished()
```

## utils/overlay_utils.py - Viewport Text Drawing

```python
from ..utils.overlay_utils import TextPainter, calculate_aligned_position

painter = TextPainter(
    text="Status", size=24,
    color=(1.0, 1.0, 1.0, 1.0),
    shadow=True, timer_duration=2.0,
)
painter.draw(x, y)

x, y = calculate_aligned_position(
    alignment="TOP_RIGHT",  # TOP_LEFT, CENTER, BOTTOM_RIGHT, etc.
    space_width, space_height,
    object_width, object_height,
    offset_x=10, offset_y=10,
)
```

## utils/anim_utils.py - Animation Frame Utilities

```python
from ..utils.anim_utils import (
    get_allowed_frames_in_range_cached,
    select_target_frame_from_list,
    find_timeline_area,
)

frames = get_allowed_frames_in_range_cached(
    context, start_frame=1, end_frame=250,
    allowed_types={"KEYFRAME", "BREAKDOWN"},
    ttl_seconds=0.1,
)
target = select_target_frame_from_list(frames, current=50, go_next=True, allow_loop=True)
```

## utils/bone_transform_utils.py - Pose Bone Analysis

```python
from ..utils.bone_transform_utils import (
    get_bone_transform_difference,
    get_bone_axes_world,
    magnitude_to_color,
    BoneTransformDifference,
)

diff: BoneTransformDifference = get_bone_transform_difference(pose_bone)
diff.rotation_angle_deg    # Rotation in degrees
diff.location_magnitude    # Translation distance
diff.has_any_change        # Quick check

origin, x_axis, y_axis, z_axis = get_bone_axes_world(pose_bone, rest_pose=False)
rgb = magnitude_to_color(angle, min_value=0, max_value=180, color_scheme="heat")
```

## operators/dopesheet_helper.py - F-Curve Utilities

```python
from .dopesheet_helper import (
    get_visible_fcurves,
    get_selected_visible_fcurves,
    get_selected_keyframes,
)

fcurves = get_visible_fcurves(context)
selected = get_selected_visible_fcurves(context)
keyframes = get_selected_keyframes(fcurve.keyframe_points)
```
