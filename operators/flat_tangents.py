# pyright: reportInvalidTypeForm=false
# bl_info = {
#     "name": "Flat Tangents for Blender",
#     "author": "Pluglug",
#     "version": (1, 1),
#     "blender": (2, 80, 0),
#     "location": "Graph Editor > Align Pie",
#     "description": "Flatten handles to match control point value while keeping original weight (length)",
#     "category": "Animation",
# }

from __future__ import annotations

import bpy
import math
from .dopesheet_helper import get_visible_fcurves
from ..utils.logging import get_logger

log = get_logger(__name__)

# --------------------------------------------------------------
# Utility
# --------------------------------------------------------------


def get_handle_type_items():
    """Returns handle-type enum items used in UI/Properties."""
    return [
        ("AUTO", "Auto", "Automatic handle type"),
        ("AUTO_CLAMPED", "Auto Clamped", "Automatic clamped handle type"),
        ("VECTOR", "Vector", "Vector handle type"),
        ("ALIGNED", "Aligned", "Aligned handle type"),
        ("FREE", "Free", "Free handle type"),
    ]


# --------------------------------------------------------------
# Operator
# --------------------------------------------------------------


class FLAT_TANGENTS_OT_operator(bpy.types.Operator):
    """Flatten selected handles keeping their original length (weighted tangents compatible)."""

    bl_idname = "anim.flat_tangents"
    bl_label = "Flat Tangents"
    bl_options = {"REGISTER", "UNDO"}

    # Optional: apply handle-type after flatten
    apply_handle_type: bpy.props.BoolProperty(
        name="Apply Handle Type",
        description="Change handle type after flatten",
        default=False,
    )

    handle_type: bpy.props.EnumProperty(  # type: ignore
        name="Handle Type",
        description="Handle type to apply after flatten",
        items=get_handle_type_items(),
        default="FREE",
    )

    # --------------------------------------------------
    # Blender callbacks
    # --------------------------------------------------

    @classmethod
    def poll(cls, context):
        # Available only in Graph Editor and when there are visible F-Curves
        return (
            context.area
            and context.area.type == "GRAPH_EDITOR"
            and get_visible_fcurves(context)
        )

    # We don't need complex invoke logic now – UI passes props directly
    def invoke(self, context, _event):  # noqa: D401 – Blender API signature
        return self.execute(context)

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    @staticmethod
    def _flatten_handle(keyframe: bpy.types.Keyframe, left: bool) -> None:
        """Move a single handle onto the keyframe's horizontal line preserving length."""
        kx, ky = keyframe.co
        handle = keyframe.handle_left if left else keyframe.handle_right

        dx = handle[0] - kx
        dy = handle[1] - ky
        length = math.hypot(dx, dy)

        log.debug(
            f"Flatten {'L' if left else 'R'} | Key:({kx:.3f},{ky:.3f}) "
            f"Handle:({handle[0]:.3f},{handle[1]:.3f}) len={length:.3f}"
        )

        # If the handle length is (almost) zero, only match Y value
        if length < 1e-6:
            new_x = handle[0]
        else:
            new_x = kx - length if left else kx + length

        new_handle_pos = (new_x, ky)
        log.debug(
            f" → NewPos:({new_handle_pos[0]:.3f},{new_handle_pos[1]:.3f}) dx={(new_handle_pos[0]-kx):.3f}"
        )

        if left:
            keyframe.handle_left = new_handle_pos
        else:
            keyframe.handle_right = new_handle_pos

    # --------------------------------------------------
    # Main execute
    # --------------------------------------------------

    def execute(self, context):  # noqa: D401 – Blender API signature
        visible_fcurves = get_visible_fcurves(context)
        if not visible_fcurves:
            self.report({"ERROR"}, "No visible F-Curves found")
            return {"CANCELLED"}

        flattened_handles = 0

        for fcurve in visible_fcurves:
            for keyframe in fcurve.keyframe_points:
                sel_cp = keyframe.select_control_point
                sel_lh = keyframe.select_left_handle
                sel_rh = keyframe.select_right_handle

                # Decide which handles should be flattened
                both = (sel_cp and not (sel_lh or sel_rh)) or (
                    not sel_cp and sel_lh and sel_rh
                )

                if both or sel_cp or sel_lh:
                    self._flatten_handle(keyframe, left=True)
                    flattened_handles += 1
                if both or sel_cp or sel_rh:
                    self._flatten_handle(keyframe, left=False)
                    flattened_handles += 1

                if self.apply_handle_type:
                    if both or sel_cp or sel_lh:
                        keyframe.handle_left_type = self.handle_type
                    if both or sel_cp or sel_rh:
                        keyframe.handle_right_type = self.handle_type

            # Update curve data after modification
            fcurve.update()

        self.report({"INFO"}, f"Flattened {flattened_handles} handles")
        return {"FINISHED"}


# CAUTION: ハンドルの「長さ」はデータ座標で保持しています。
#          Graph Editor は X=フレーム, Y=値 でスケールが異なるため
#          ズームレベルによっては視覚上ハンドルが短く見えることがあります。
