# pyright: reportInvalidTypeForm=false
import bpy
import blf
import re
from time import time

from .addon import get_prefs
from . import constants as CC
from .utils.logging import get_logger
from .operators.dopesheet_helper import get_selected_visible_fcurves

log = get_logger(__name__)


def blf_size(font_id, size, *args, **kwargs):
    blf.size(font_id, size)


# TODO: Utilsへ移動
def multiton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.reset(duration)

    def update(self):
        current_time = time()
        elapsed_time = current_time - self.start_time
        self.remaining_time -= elapsed_time
        self.start_time = current_time

        return self.remaining_time <= 0

    def reset(self, duration):
        self.duration = duration
        self.remaining_time = duration
        self.start_time = time()

    # def remaining_percentage(self):
    #     # Transitions from 100 to 0
    #     return max(0, self.remaining_time / self.duration * 100)

    def elapsed_ratio(self):
        """Returns the ratio of elapsed time to total duration."""
        return max(0, min(1, (self.duration - self.remaining_time) / self.duration))

    def is_finished(self):
        return self.remaining_time <= 0


def calculate_aligned_position(
    alignment: str,
    space_width: float,
    space_height: float,
    object_width: float,
    object_height: float,
    offset_x: int,
    offset_y: int,
) -> tuple[float, float]:
    """
    Calculate the aligned position for an object within a given area based on the alignment and offsets.

    Parameters:
        alignment: The object alignment within the area. enum in OVERLAY_ALIGNMENT_ITEMS
        space_width: The width of the area where the object will be displayed.
        space_height: The height of the area where the object will be displayed.
        object_width: The width of the object.
        object_height: The height of the object.
        offset_x: The horizontal offset from the aligned position.
        offset_y: The vertical offset from the aligned position.

    Returns:
        A tuple of (x, y) coordinates for the object position.
    """
    valid_alignments = {item[0] for item in CC.OVERLAY_ALIGNMENT_ITEMS}
    if alignment not in valid_alignments:
        raise ValueError(f"Invalid alignment: {alignment}")

    if "TOP" in alignment:
        y = space_height - object_height - offset_y
    elif "BOTTOM" in alignment:
        y = offset_y
    else:  # Center
        y = (space_height - object_height) / 2

    if "LEFT" in alignment:
        x = offset_x
    elif "RIGHT" in alignment:
        x = space_width - object_width - offset_x
    else:  # Center
        x = (space_width - object_width) / 2

    return x, y


class TextPainter:
    """Manage text styles and displey times."""

    def __init__(
        self,
        text="DEBUG TEXT",
        font_id=0,
        size=24,
        color=(1.0, 1.0, 1.0, 1.0),  # pr.themes[0].view_3d.object_active
        shadow=True,
        shadow_color=(0.0, 0.0, 0.0, 1.0),
        shadow_blur=3,
        shadow_offset_x=2,
        shadow_offset_y=2,
        timer_duration=1.0,
        fade_start_ratio=0.3,
    ):
        self._text = text
        self.font_id = font_id
        self._size = size
        self.color = color
        self.shadow = shadow
        self.shadow_color = shadow_color
        self.shadow_blur = shadow_blur
        self.shadow_offset_x = shadow_offset_x
        self.shadow_offset_y = shadow_offset_y
        self.timer_duration = timer_duration
        self.timer = Timer(timer_duration)
        self.fade_start_ratio = fade_start_ratio
        self.update_dimensions()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.update_dimensions()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value
        self.update_dimensions()

    @property
    def dimensions(self) -> tuple[float, float]:
        """Text dimensions (width, height)"""
        return self._dimensions

    def update_dimensions(self) -> "TextPainter":
        blf_size(self.font_id, self.size)
        self._dimensions = blf.dimensions(self.font_id, self.text)
        return self

    # def set_timer(self, duration):  # Delete if not needed
    #     self.timer_duration = duration
    #     if self.timer is None:
    #         self.timer = Timer(duration)
    #     else:
    #         self.timer.reset(duration)
    #     return self

    def calculate_alpha(
        self, color: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        """Calculate alpha based on the timer's remaining time and the fade start ratio."""
        elapsed_ratio = self.timer.elapsed_ratio()
        if elapsed_ratio < self.fade_start_ratio:
            return color
        else:
            fade_effective_ratio = (elapsed_ratio - self.fade_start_ratio) / (
                1 - self.fade_start_ratio
            )
            alpha = color[3] * (1 - fade_effective_ratio)
            return color[:3] + (alpha,)

    def draw(self, x, y):
        if not self.timer.is_finished():
            blf_size(self.font_id, self.size)
            blf.color(self.font_id, *self.calculate_alpha(self.color))

            if self.shadow:
                blf.enable(self.font_id, blf.SHADOW)
                blf.shadow(
                    self.font_id,
                    self.shadow_blur,
                    *self.calculate_alpha(self.shadow_color),
                )
                blf.shadow_offset(
                    self.font_id, self.shadow_offset_x, self.shadow_offset_y
                )
            else:
                blf.disable(self.font_id, blf.SHADOW)

            blf.position(self.font_id, x, y, z=0)
            blf.draw(self.font_id, self.text)

    @classmethod
    def from_settings(cls, settings: "TextOverlaySettings") -> "TextPainter":
        return cls(
            size=settings.size,
            color=settings.color,
            shadow=settings.use_shadow,
            shadow_color=settings.shadow_color,
            shadow_blur=settings.shadow_blur,
            shadow_offset_x=settings.shadow_offset_x,
            shadow_offset_y=settings.shadow_offset_y,
            timer_duration=settings.duration,
            fade_start_ratio=0.3,  # TODO: Make this a setting
        )

    @classmethod
    def from_settings_and_text(
        cls, settings: "TextOverlaySettings", text: str
    ) -> "TextPainter":
        painter = cls.from_settings(settings)
        painter.text = text
        return painter


class DrawingSpace:
    def __init__(
        self,
        space_type: bpy.types.Space,
    ):
        pass
        # 行間のオフセット
        # self.line_offset = 5
        # alignment='TOP',
        # offset_x=10,
        # offset_y=10,

    def generate_text_lines(self, context):
        pass


# drawing_spaces = {}


# bpy.context.space_dataがtp.Spaceのインスタンスなので、マッピングは不要
# NOTE: The current space, may be None in background-mode,
# when the cursor is outside the window or when using menu-search
# def add_space(id, space_type_name):
#     space_type = getattr(bpy.types, space_type_name, None)
#     if not space_type:
#         print(f"Space type '{space_type_name}' not found.")
#         return

#     drawing_spaces[id] = DrawingSpace(space_type)


def _draw_callback(overlay_text):
    pass


class TextOverlaySettings(bpy.types.PropertyGroup):
    show_text: bpy.props.BoolProperty(
        name="Show Text",
        description="Notify selected channel name",
        default=True,
    )
    size: bpy.props.IntProperty(
        name="Font Size",
        description="Font size",
        default=24,
        min=10,
        max=50,
        options={"SKIP_SAVE"},
        # update=,
    )
    color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0, 1.0, 1.0, 1.0),
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
    )
    alignment: bpy.props.EnumProperty(
        name="Alignment",
        description="Text alignment on area",
        items=CC.OVERLAY_ALIGNMENT_ITEMS,
        default="TOP",
    )
    duration: bpy.props.FloatProperty(
        name="Duration",
        description="Duration of the text display",
        default=1.0,
        min=0.0,
        subtype="TIME_ABSOLUTE",
    )
    offset_x: bpy.props.IntProperty(
        name="Offset X",
        description="Offset from area edge",
        subtype="PIXEL",
        default=10,
        min=0,
    )
    offset_y: bpy.props.IntProperty(
        name="Offset Y",
        description="Offset from area edge",
        subtype="PIXEL",
        default=10,
        min=0,
    )
    use_shadow: bpy.props.BoolProperty(
        name="Use Shadow",
        description="Use shadow for text",
        default=True,
    )
    shadow_color: bpy.props.FloatVectorProperty(
        name="Shadow Color",
        description="Shadow color",
        default=(0.0, 0.0, 0.0, 1.0),
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
    )
    shadow_blur: bpy.props.IntProperty(
        name="Shadow Blur",
        description="Shadow blur level. can be 3, 5 or 0",
        subtype="PIXEL",
        default=3,
        min=0,
        max=5,
    )
    shadow_offset_x: bpy.props.IntProperty(
        name="Shadow Offset X",
        description="Shadow offset from text",
        subtype="PIXEL",
        default=2,
        min=0,
    )
    shadow_offset_y: bpy.props.IntProperty(
        name="Shadow Offset Y",
        description="Shadow offset from text",
        subtype="PIXEL",
        default=2,
        min=0,
    )
    max_display_count: bpy.props.IntProperty(
        name="Max Display Count",
        description="Maximum display count",
        default=3,
        min=1,
        max=10,
    )

    def draw(self, context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()

        col.label(text="Text Overlay Settings", icon="IMAGE_ALPHA")
        # layout.prop(self, "show_text")
        col.prop(self, "size")
        col.prop(self, "color")
        col.prop(self, "alignment")
        col.prop(self, "duration")
        col.prop(self, "offset_x")
        col.prop(self, "offset_y")
        col.prop(self, "max_display_count")

        col.separator()

        col.prop(self, "use_shadow")
        sub = col.column()
        sub.active = self.use_shadow
        sub.prop(self, "shadow_color")
        sub.prop(self, "shadow_blur")
        sub.prop(self, "shadow_offset_x")
        sub.prop(self, "shadow_offset_y")


# function to channel info


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


def generate_text_lines(context):
    """
    選択中のvisible_fcurvesから最大N個のカーブ名と色を返す。
    超過分はサマリ行で表示。
    戻り値: [(text, color), ...]
    """
    log.debug("generate_text_lines (selected_visible_fcurves) called")
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
    return lines


class ChannelInfoToDisplay(bpy.types.PropertyGroup):
    object_name: bpy.props.BoolProperty(
        name="Object Name",
        description="Display object name",
        default=True,
    )
    action_name: bpy.props.BoolProperty(
        name="Action Name",
        description="Display action name",
        default=True,
    )
    group_name: bpy.props.BoolProperty(
        name="Group Name",
        description="Display group name",
        default=True,
    )
    channel_name: bpy.props.BoolProperty(
        name="Channel Name",
        description="Display channel name",
        default=True,
    )

    def draw(self, context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(heading="Channel Info to Display")

        col.prop(self, "object_name")
        col.prop(self, "action_name")
        col.prop(self, "group_name")
        col.prop(self, "channel_name")


def draw_callback_wrapper(*args, **kwargs):
    context = bpy.context
    TextDisplayHandler.draw_callback(context)


class TextDisplayHandler:
    def __init__(self):
        self.draw_handler = None

    def start(self, context):
        if self.draw_handler is None:
            self.draw_handler = bpy.types.SpaceGraphEditor.draw_handler_add(
                draw_callback_wrapper, (), "WINDOW", "POST_PIXEL"
            )

    def stop(self):
        if self.draw_handler is not None:
            bpy.types.SpaceGraphEditor.draw_handler_remove(self.draw_handler, "WINDOW")
            self.draw_handler = None

    def is_active(self):
        return self.draw_handler is not None

    @staticmethod
    def draw_callback(context):
        if not context.region:
            return
        pr = get_prefs(context)
        text_lines = generate_text_lines(context)
        if not pr.overlay.show_text or not text_lines:
            return
        font_id = 0
        blf_size(font_id, pr.overlay.size)
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


text_display_handler = TextDisplayHandler()


class TEXT_OT_activate_handler(bpy.types.Operator):
    """Activate the text display handler"""

    bl_idname = "text.activate_handler"
    bl_label = "Activate Text Handler"

    @classmethod
    def poll(cls, context):
        return not text_display_handler.is_active()

    def execute(self, context):
        text_display_handler.start(context)
        return {"FINISHED"}


class TEXT_OT_deactivate_handler(bpy.types.Operator):
    """Deactivate the text display handler"""

    bl_idname = "text.deactivate_handler"
    bl_label = "Deactivate Text Handler"

    @classmethod
    def poll(cls, context):
        return text_display_handler.is_active()

    def execute(self, context):
        text_display_handler.stop()
        return {"FINISHED"}


if __name__ == "__main__":
    pass
