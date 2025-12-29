# Adding Settings/Preferences

## File Header Required

Files defining PropertyGroup or Preferences **must** add at the top:

```python
# pyright: reportInvalidTypeForm=false
```

## Creating a PropertyGroup

1. Create a `PropertyGroup` in your module:

```python
# pyright: reportInvalidTypeForm=false
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty

class MyOperatorSettings(PropertyGroup):
    enabled: BoolProperty(default=True)
    count: IntProperty(default=5, min=1, max=100)

    def draw(self, context, layout):
        layout.prop(self, "enabled")
        layout.prop(self, "count")
```

2. Add `PointerProperty` to `MonKeyPreferences` in `preferences.py`:

```python
from .operators.my_operator import MyOperatorSettings

class MonKeyPreferences(AddonPreferences):
    my_settings: PointerProperty(type=MyOperatorSettings)
```

3. Access via:

```python
from ..addon import get_prefs

settings = get_prefs(context).my_settings
if settings.enabled:
    # do something
```

## Naming Convention

- **PropertyGroups**: `CamelCaseSettings` (e.g., `ChannelSelectionOverlaySettings`)
