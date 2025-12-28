# MonKey Addon Overview

**MonKey** (Graph Monkey) is a Blender animation addon that enhances Graph Editor workflow with keyframe manipulation tools, playback controls, and pose visualization.

- **Version**: 0.9.0
- **Blender**: 2.80+ (some features require 4.4+)
- **Language**: Comments use both Japanese and English - either is acceptable

## Directory Structure

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

## Key Entry Points

- **`addon.get_prefs(context)`**: Get addon preferences
- **`get_logger(__name__)`**: Create module logger (from `utils.logging`)
- **`ic(icon_name)`**: Icon with version fallback (from `utils.ui_utils`)
