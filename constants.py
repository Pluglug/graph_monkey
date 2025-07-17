from typing import Literal

from bpy.app import version as BLENDER_VERSION
from .utils.logging import get_logger

SINCE_4_0_0 = BLENDER_VERSION >= (4, 0, 0)

log = get_logger(__name__)

OVERLAY_ALIGNMENT_ITEMS = [
    ("TOP", "Top", ""),
    ("TOP_LEFT", "Top Left", ""),
    ("TOP_RIGHT", "Top Right", ""),
    ("BOTTOM", "Bottom", ""),
    ("BOTTOM_LEFT", "Bottom Left", ""),
    ("BOTTOM_RIGHT", "Bottom Right", ""),
]

# スペースタイプの型定義
SpaceType = Literal[
    "EMPTY",
    "VIEW_3D",
    "IMAGE_EDITOR",
    "NODE_EDITOR",
    "SEQUENCE_EDITOR",
    "CLIP_EDITOR",
    "MOTION_TRACKING",
    "ANIMATION",
    "DOPESHEET_EDITOR",
    "GRAPH_EDITOR",
    "NLA_EDITOR",
    "SCRIPTING",
    "TEXT_EDITOR",
    "CONSOLE",
    "INFO",
    "TOPBAR",
    "STATUSBAR",
    "OUTLINER",
    "PROPERTIES",
    "FILE_BROWSER",
    "SPREADSHEET",
    "PREFERENCES",
]

# リージョンタイプの型定義
RegionType = Literal[
    "WINDOW",
    "HEADER",
    "CHANNELS",
    "TEMPORARY",
    "UI",
    "TOOLS",
    "TOOL_PROPS",
    "ASSET_SHELF",
    "PREVIEW",
    "HUD",
    "NAVIGATION_BAR",
    "EXECUTE",
    "FOOTER",
    "TOOL_HEADER",
    "XR",
]

SPACE_TYPE_ITEMS = [
    ("EMPTY", "Empty", "Empty"),
    ("VIEW_3D", "3D Viewport", "3D Viewport"),
    ("IMAGE_EDITOR", "Image Editor", "Image Editor"),
    ("NODE_EDITOR", "Node Editor", "Node Editor"),
    ("SEQUENCE_EDITOR", "Video Sequencer", "Video Sequencer"),
    ("CLIP_EDITOR", "Movie Clip Editor", "Movie Clip Editor"),
    ("MOTION_TRACKING", "Motion Tracking", "Motion Tracking"),
    ("ANIMATION", "Animation", "Animation"),
    ("DOPESHEET_EDITOR", "Dope Sheet", "Dope Sheet"),
    ("GRAPH_EDITOR", "Graph Editor", "Graph Editor"),
    ("NLA_EDITOR", "Nonlinear Animation", "Nonlinear Animation"),
    ("SCRIPTING", "Scripting", "Scripting"),
    ("TEXT_EDITOR", "Text Editor", "Text Editor"),
    ("CONSOLE", "Console", "Console"),
    ("INFO", "Info", "Info"),
    ("TOPBAR", "Top Bar", "Top Bar"),
    ("STATUSBAR", "Status Bar", "Status Bar"),
    ("OUTLINER", "Outliner", "Outliner"),
    ("PROPERTIES", "Properties", "Properties"),
    ("FILE_BROWSER", "File Browser", "File Browser"),
    ("SPREADSHEET", "Spreadsheet", "Spreadsheet"),
    ("PREFERENCES", "Preferences", "Preferences"),
]  # 特に使ってない

REGION_TYPE_ITEMS = [
    ("WINDOW", "Window", "Window"),
    ("HEADER", "Header", "Header"),
    ("CHANNELS", "Channels", "Channels"),
    ("TEMPORARY", "Temporary", "Temporary"),
    ("UI", "Sidebar", "Sidebar"),
    ("TOOLS", "Tools", "Tools"),
    ("TOOL_PROPS", "Tool Properties", "Tool Properties"),
    ("ASSET_SHELF", "Asset Shelf", "Asset Shelf"),
    ("PREVIEW", "Preview", "Preview"),
    ("HUD", "Floating Region", "Floating Region"),
    ("NAVIGATION_BAR", "Navigation Bar", "Navigation Bar"),
    ("EXECUTE", "Execute Buttons", "Execute Buttons"),
    ("FOOTER", "Footer", "Footer"),
    ("TOOL_HEADER", "Tool Header", "Tool Header"),
    ("XR", "XR", "XR"),
]  # 特に使ってない

EVENT_DIRECTION_ITEMS = [
    ("ANY", "Any", "Any"),
    ("NORTH", "North", "North"),
    ("NORTH_EAST", "North-East", "North-East"),
    ("EAST", "East", "East"),
    ("SOUTH_EAST", "South-East", "South-East"),
    ("SOUTH", "South", "South"),
    ("SOUTH_WEST", "South-West", "South-West"),
    ("WEST", "West", "West"),
    ("NORTH_WEST", "North-West", "North-West"),
]  # 特に使ってない

EVENT_VALUE_ITEMS = [
    ("ANY", "Any", "Any"),
    ("PRESS", "Press", "Press"),
    ("RELEASE", "Release", "Release"),
    ("CLICK", "Click", "Click"),
    ("DOUBLE_CLICK", "Double Click", "Double Click"),
    ("CLICK_DRAG", "Click Drag", "Click Drag"),
    ("NOTHING", "Nothing", "Nothing"),
]  # 特に使ってない
