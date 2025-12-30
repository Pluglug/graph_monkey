# Graph Monkey

Animation workflow toolkit for Blender's Graph Editor. Keyboard-driven keyframe editing and channel management.

[日本語ドキュメント](docs/USER_GUIDE_JA.md)

![WASD Navigation](docs/images/wasd_navigation.gif)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Pluglug)

[![Download Latest Release](https://img.shields.io/badge/Download-Latest%20Release-2ea44f?style=for-the-badge\&logo=github)](../../releases)

---

## Quick Start

### Keyboard Layout

<img src="docs/images/keyboard_layout.png" width="50%">

| Color | Key | Function |
|-------|-----|----------|
| 🔴 | `Alt + WASD/QE` | [Keyframe/Channel/Handle selection](#wasd-navigation) |
| 🟠 | `Y` (hold) | [Channel Navigator](#channel-navigator) |
| 🟢 | `1234` | [Frame jump](#frame-navigation--peek) (works in 3D View too) |
| 🔵 | `F` | [Focus on selected curve](#focus) |
| 🟡 | `Shift + T/C` | [Pie menus](#pie-menus) |

---

## WASD Navigation

Core feature for fast keyframe editing in Graph Editor. **Edit keyframes entirely from keyboard** without touching the mouse.

| Key | Action |
|-----|--------|
| `Alt + A` / `Alt + D` | Move to left/right keyframe |
| `Alt + W` / `Alt + S` | Move to upper/lower channel |
| `+ Shift` | Extend selection |

<img src="docs/images/wasd_navigation.gif" width="70%">

### Handle Selection

| Key | Action |
|-----|--------|
| `Alt + Q` / `Alt + E` | Select left/right handle |
| `+ Shift` | Extend selection |

<img src="docs/images/handle_selection.gif" width="70%">

### Focus

| Key | Action |
|-----|--------|
| `F` | Focus on selected curve within playback range |
| `Alt + F` | Show entire selected curve |

### Auto Focus

<img src="docs/images/wasd_autofocus.gif" width="70%">

**Auto Focus on Channel Change**: Automatically focuses on the curve when switching channels with W/S.

**Auto Follow Current Frame**: Current frame follows when moving to a keyframe with A/D (single selection only).

---

## Channel Navigator

**Hold** the `Y` key to show an interactive channel management popup.

<img src="docs/images/channel_navigator.gif" width="70%">

| Action | Function |
|--------|----------|
| Mouse hover | Switch channel selection |
| `Ctrl + Click` | Solo display |
| `H` / `L` / `M` | Toggle Hide / Lock / Mute |
| Mouse wheel | Scroll (when 8+ channels) |

<img src="docs/images/channel_navigator_autofocus.gif" width="70%">

---

## Frame Navigation & Peek

Frame navigation that works from **any editor** - Timeline, Dopesheet, Graph Editor, or 3D View.

### Frame Jump

| Key | Action |
|-----|--------|
| `1` / `2` | Step back / forward 1 frame |
| `3` / `4` | Jump to previous / next keyframe |

<img src="docs/images/keyframe_jump_peek.gif" width="70%">

### Keyframe Type Filter

Filter by keyframe type (KEYFRAME, BREAKDOWN, EXTREME, etc.) in Timeline/Dopesheet header.

<img src="docs/images/keyframe_filter.gif" width="70%">

### Peek

`Shift + 3/4` **temporarily previews** adjacent keyframes. Quick pose comparison like flipping pages.

```mermaid
flowchart LR
    A["Shift+3/4 press"] --> B["Previewing"]
    B --> C{"Release order"}
    C -->|"Both together"| D["Return to original"]
    C -->|"Shift first"| E["Stay at destination"]
```

**During Peek**: `1`/`2` for additional offset, `Q` to reset

---

## Pie Menus

### Key Align Pie (Shift + T)

Align keyframes in Graph Editor.

<img src="docs/images/key_align_pie.gif" width="70%">

| Item | Action |
|------|--------|
| Left / Right | Align on frame axis |
| Top / Bottom | Align on value axis |
| Flat | Flatten handles (weighted handles supported) |

### Transform Pie (Shift + C)

Quick access to Graph Editor transform settings.

<img src="docs/images/config_pie.png" width="50%">

Toggle Pivot Point (Center / Individual / Cursor) and Proportional editing.

---

## UI Extensions

### Action Toolbar

<img src="docs/images/graph_topbar.png" width="100%">

Action management buttons in Graph Editor header. Access Dopesheet Action Editor features directly.

### Interpolation Toggle

Icon buttons (CONSTANT / LINEAR / BEZIER) in Graph Editor header for quick interpolation type switching.

### F-Curves Panel

F-Curves settings in Graph Editor's N-panel (View tab). Change interpolation without opening Preferences.

### Playback Speed Controller

<img src="docs/images/playback_speed_controller.png" width="70%">

Speed control (0.01x - 9.0x) with preset buttons (¼x/½x/1x/2x). Click Store to save original range before adjusting.

### Channel Selection Overlay

<img src="docs/images/channel_overlay.png" width="50%">

Shows selected F-Curve name on Graph Editor.

### Sync Visible Range

<img src="docs/images/sync_visible_range.png" width="50%">

Lock visible range across time-based editors. Click the 🔒 icon in header. Scroll/zoom in one editor syncs others.

### Channel Expand/Collapse

| Key | Action |
|-----|--------|
| `Shift + A` | Expand all channels |
| `Ctrl + Shift + A` | Collapse all channels |

---

## Utilities

### Run Scripts

**File → Run Scripts** menu to execute Python scripts stored in blend files without opening Text Editor.

<img src="docs/images/run_scripts.png" width="100%">

### Clean Animation Preview

<img src="docs/images/clean_animation_preview.gif" width="70%">

Hide bone names, axes, meshes etc. for clean animation preview.

---

## Pose Mode Tools

### Pose Transform Visualizer

Visualize bone rotation/translation in 3D View. Toggle with `V` key.

<img src="docs/images/pose_visualizer.gif" width="90%">

Arcs show rotation, arrows show translation. Color schemes: Heat / Cool / Grayscale.

### Bone Collection Solo

Solo the bone collection of selected bones (Blender 4.0+).

| Key | Action |
|-----|--------|
| `/` | Solo selected bone's collection |
| `Alt + /` | Unsolo |

<img src="docs/images/bone_collection_solo.gif" width="70%">

---

## Settings

**Edit → Preferences → Add-ons → Graph Monkey**

### Graph Editor

| Setting | Default | Description |
|---------|---------|-------------|
| Auto Focus on Channel Change | ON | Auto focus after channel move |
| Auto Follow Current Frame | OFF | Current frame follows keyframe selection |

### Channel Navigator

| Setting | Default | Description |
|---------|---------|-------------|
| Box Height / Width | 28 / 280 | Popup size |
| Text Size | 12 | Text size |
| Max Display Count | 8 | Max visible channels |

### Channel Overlay

| Setting | Default | Description |
|---------|---------|-------------|
| Font Size | 24 | Font size |
| Alignment | TOP_RIGHT | Display position |

### Pose Visualizer

| Setting | Default | Description |
|---------|---------|-------------|
| Show Rotation / Location | ON / ON | Visualize rotation/translation |
| Color Scheme | Heat | Heat / Cool / Grayscale |

---

## Installation

1. Download the [latest release](../../releases) zip
2. In Blender: Edit → Preferences → Add-ons → Install
3. Select the downloaded zip file
4. Enable "Graph Monkey"

## License

GPL-3.0 - See [LICENSE](LICENSE) for details.
