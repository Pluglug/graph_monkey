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
