from time import time

import blf
import bpy

from ..constants import OVERLAY_ALIGNMENT_ITEMS
from .timer import Timer


def multiton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


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
    valid_alignments = {item[0] for item in OVERLAY_ALIGNMENT_ITEMS}
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
        blf.size(self.font_id, self.size)
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
            blf.size(self.font_id, self.size)
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
    def from_settings(cls, settings) -> "TextPainter":
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
    def from_settings_and_text(cls, settings, text: str) -> "TextPainter":
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

    def generate_channel_selection_overlay_lines(self, context):
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
