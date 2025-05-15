from bpy.app import version as BLENDER_VERSION

SINCE_4_0_0 = BLENDER_VERSION >= (4, 0, 0)

OVERLAY_ALIGNMENT_ITEMS = [
    ("TOP", "Top", ""),
    ("TOP_LEFT", "Top Left", ""),
    ("TOP_RIGHT", "Top Right", ""),
    ("BOTTOM", "Bottom", ""),
    ("BOTTOM_LEFT", "Bottom Left", ""),
    ("BOTTOM_RIGHT", "Bottom Right", ""),
]
