from bpy.app import version as BL_VERSION
from bpy.types import UILayout

from .logging import get_logger

log = get_logger(__name__)


ICON_ENUM_ITEMS = UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items


def ic(icon):
    if not icon:
        return icon

    if icon in ICON_ENUM_ITEMS:
        return icon

    if icon.startswith("SEQUENCE_COLOR_"):  # 4.4+
        return icon.replace("SEQUENCE_COLOR_", "STRIP_COLOR_")

    ICON_ALTERNATIVES = {
        "GREASEPENCIL_LAYER_GROUP": "TEXT",
        "EVENT_NDOF_BUTTON_1": "ONIONSKIN_ON",
    }

    if icon in ICON_ALTERNATIVES:
        alt_icon = ICON_ALTERNATIVES[icon]
        return alt_icon

    log.warning(f"Icon not found: {icon}")
    return "BLENDER"


def ic_rb(value):
    return ic("RADIOBUT_ON" if value else "RADIOBUT_OFF")


def ic_cb(value):
    return ic("CHECKBOX_HLT" if value else "CHECKBOX_DEHLT")


def ic_fb(value):
    return ic("SOLO_ON" if value else "SOLO_OFF")


def ic_eye(value):
    return ic("HIDE_OFF" if value else "HIDE_ON")


def ui_prop(layout, data, property, **kwargs):
    if BL_VERSION < (4, 1, 0) and "placeholder" in kwargs:
        del kwargs["placeholder"]

    layout.prop(data, property, **kwargs)
