# pyright: reportInvalidTypeForm=false
import re

import blf
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, IntProperty
from bpy.types import Operator

from ..addon import get_prefs
from ..constants import OVERLAY_ALIGNMENT_ITEMS
from ..operators.dopesheet_helper import get_selected_visible_fcurves
from ..utils.logging import get_logger
from ..utils.overlay_utils import calculate_aligned_position

log = get_logger(__name__)


def convert_data_path_to_readable(channel_data_path: str) -> str:
    log.debug(f"convert_data_path_to_readable(\n    '{channel_data_path}')")
    replace_list = [
        ('["', " "),
        ('"].', " < "),
        ("_", " "),
    ]
    for old, new in replace_list:
        channel_data_path = channel_data_path.replace(old, new)

    readable_data_path = re.sub(r"(\.)([A-Z])", r"\1 \2", channel_data_path)
    readable_data_path = " ".join(
        word.capitalize() for word in readable_data_path.split(" ")
    )

    log.debug(f"readable_data_path: {readable_data_path}")
    return readable_data_path


def gen_channel_info_line(fcurve):
    """
    Fカーブから人間が分かりやすいチャンネル名を生成し、色も返す。
    """
    data_path = fcurve.data_path
    idx = fcurve.array_index
    group = fcurve.group.name if fcurve.group else ""
    color = tuple(fcurve.color) if hasattr(fcurve, "color") else (1.0, 1.0, 1.0, 1.0)

    # 配列プロパティのラベル化
    array_labels = {
        "location": ["X Location", "Y Location", "Z Location"],
        "scale": ["X Scale", "Y Scale", "Z Scale"],
        "rotation_euler": ["X Euler Rotation", "Y Euler Rotation", "Z Euler Rotation"],
        "rotation_quaternion": [
            "W Quaternion Rotation",
            "X Quaternion Rotation",
            "Y Quaternion Rotation",
            "Z Quaternion Rotation",
        ],
        "delta_location": ["X Delta Location", "Y Delta Location", "Z Delta Location"],
        "delta_scale": ["X Delta Scale", "Y Delta Scale", "Z Delta Scale"],
        "delta_rotation_euler": [
            "X Delta Euler Rotation",
            "Y Delta Euler Rotation",
            "Z Delta Euler Rotation",
        ],
        "delta_rotation_quaternion": [
            "W Delta Quaternion Rotation",
            "X Delta Quaternion Rotation",
            "Y Delta Quaternion Rotation",
            "Z Delta Quaternion Rotation",
        ],
    }
    # ドット区切りで最後のワードをキーにする
    last_key = data_path.split(".")[-1]
    if last_key in array_labels and idx < len(array_labels[last_key]):
        channel_name = array_labels[last_key][idx]
    else:
        channel_name = convert_data_path_to_readable(data_path)
        if hasattr(fcurve, "array_index") and fcurve.array_index != 0:
            channel_name += f"[{fcurve.array_index}]"
    if group:
        channel_name = f"{group}: {channel_name}"
    return channel_name, color


def get_fcurve_display_color(fcurve, alpha=1.0):
    color = tuple(fcurve.color) if hasattr(fcurve, "color") else (1.0, 1.0, 1.0)
    if len(color) == 3:
        color = (color[0], color[1], color[2], alpha)
    elif len(color) == 4:
        color = (color[0], color[1], color[2], alpha)
    else:
        color = (1.0, 1.0, 1.0, alpha)
    return color


def gen_channel_selection_overlay_lines(context):
    """
    選択中のvisible_fcurvesから最大N個のカーブ名と色を返す。
    超過分はサマリ行で表示。
    戻り値: [(text, color), ...]
    """
    log.debug("gen_channel_selection_overlay_lines (selected_visible_fcurves) called")
    pr = get_prefs(context)
    selected_fcurves = get_selected_visible_fcurves(context)
    if not selected_fcurves:
        return []
    max_count = getattr(pr.overlay, "max_display_count", 3)
    lines = []
    for fcurve in selected_fcurves[:max_count]:
        text, _ = gen_channel_info_line(fcurve)
        color = get_fcurve_display_color(fcurve, alpha=1.0)
        lines.append((text, color))
    if len(selected_fcurves) > max_count:
        lines.append(
            (f"...{len(selected_fcurves) - max_count} more", (1.0, 1.0, 1.0, 1.0))
        )

    if "BOTTOM" in pr.overlay.alignment:
        lines.reverse()

    return lines


class ChannelSelectionOverlaySettings(bpy.types.PropertyGroup):
    show_text: BoolProperty(
        name="Show Text",
        description="Notify selected channel name",
        default=True,
    )
    size: IntProperty(
        name="Font Size",
        description="Font size",
        default=24,
        min=10,
        max=50,
        options={"SKIP_SAVE"},
    )
    color: FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0, 1.0, 1.0, 1.0),
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
    )
    alignment: EnumProperty(
        name="Alignment",
        description="Text alignment on area",
        items=OVERLAY_ALIGNMENT_ITEMS,
        default="TOP",
    )
    # duration: FloatProperty(
    #     name="Duration",
    #     description="Duration of the text display",
    #     default=1.0,
    #     min=0.0,
    #     subtype="TIME_ABSOLUTE",
    # )
    offset_x: IntProperty(
        name="Offset X",
        description="Offset from area edge",
        subtype="PIXEL",
        default=10,
        min=0,
    )
    offset_y: IntProperty(
        name="Offset Y",
        description="Offset from area edge",
        subtype="PIXEL",
        default=50,
        min=0,
    )
    # use_shadow: BoolProperty(
    #     name="Use Shadow",
    #     description="Use shadow for text",
    #     default=True,
    # )
    # shadow_color: FloatVectorProperty(
    #     name="Shadow Color",
    #     description="Shadow color",
    #     default=(0.0, 0.0, 0.0, 1.0),
    #     subtype="COLOR",
    #     size=4,
    #     min=0.0,
    #     max=1.0,
    # )
    # shadow_blur: IntProperty(
    #     name="Shadow Blur",
    #     description="Shadow blur level. can be 3, 5 or 0",
    #     subtype="PIXEL",
    #     default=3,
    #     min=0,
    #     max=5,
    # )
    # shadow_offset_x: IntProperty(
    #     name="Shadow Offset X",
    #     description="Shadow offset from text",
    #     subtype="PIXEL",
    #     default=2,
    #     min=0,
    # )
    # shadow_offset_y: IntProperty(
    #     name="Shadow Offset Y",
    #     description="Shadow offset from text",
    #     subtype="PIXEL",
    #     default=2,
    #     min=0,
    # )
    max_display_count: IntProperty(
        name="Max Display Count",
        description="Maximum display count",
        default=3,
        min=1,
        max=10,
    )

    def draw(self, _context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()

        col.label(text="Text Overlay Settings", icon="IMAGE_ALPHA")
        col.prop(self, "show_text")
        col.prop(self, "size")
        col.prop(self, "color")
        col.prop(self, "alignment")
        # col.prop(self, "duration")
        col.prop(self, "offset_x")
        col.prop(self, "offset_y")
        col.prop(self, "max_display_count")

        # col.separator()

        # col.prop(self, "use_shadow")
        # sub = col.column()
        # sub.active = self.use_shadow
        # sub.prop(self, "shadow_color")
        # sub.prop(self, "shadow_blur")
        # sub.prop(self, "shadow_offset_x")
        # sub.prop(self, "shadow_offset_y")


class ChannelSelectionOverlayHandler:
    def __init__(self):
        self.draw_handler = None

    def start(self):
        if self.draw_handler is None:
            self.draw_handler = bpy.types.SpaceGraphEditor.draw_handler_add(
                self._draw_callback_wrapper, (), "WINDOW", "POST_PIXEL"
            )

    def stop(self):
        if self.draw_handler is not None:
            bpy.types.SpaceGraphEditor.draw_handler_remove(self.draw_handler, "WINDOW")
            self.draw_handler = None

    def is_active(self):
        return self.draw_handler is not None

    def _draw_callback_wrapper(self, *_args, **_kwargs):
        context = bpy.context
        self._draw_callback(context)

    def _draw_callback(self, context):
        if not context.region:
            return
        pr = get_prefs(context)
        text_lines = gen_channel_selection_overlay_lines(context)
        if not pr.overlay.show_text or not text_lines:
            return
        font_id = 0
        blf.size(font_id, pr.overlay.size)
        y_offset = pr.overlay.offset_y
        for text, color in text_lines:
            # 色が3要素ならalpha=1.0を補う
            if len(color) == 3:
                color = (color[0], color[1], color[2], 1.0)
            # 減衰処理（仮: alpha=1.0のまま）
            alpha = color[3]
            x, y = calculate_aligned_position(
                pr.overlay.alignment,
                context.region.width,
                context.region.height,
                blf.dimensions(font_id, text)[0],
                blf.dimensions(font_id, text)[1],
                pr.overlay.offset_x,
                y_offset,
            )
            blf.color(font_id, color[0], color[1], color[2], alpha)
            blf.position(font_id, x, y, 0)
            blf.draw(font_id, text)
            text_height = blf.dimensions(font_id, text)[1]
            y_offset += text_height + 5


channel_selection_overlay_handler = ChannelSelectionOverlayHandler()


class MONKEY_OT_toggle_channel_selection_overlay(Operator):
    """Toggle the channel selection overlay"""

    bl_idname = "graph.toggle_channel_selection_overlay"
    bl_label = "Toggle Channel Selection Overlay"

    active: BoolProperty(default=False)

    def execute(self, _context):
        if self.active:
            channel_selection_overlay_handler.start()
        else:
            channel_selection_overlay_handler.stop()
        return {"FINISHED"}


def register():
    channel_selection_overlay_handler.start()


def unregister():
    channel_selection_overlay_handler.stop()
