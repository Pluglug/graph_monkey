from bpy.types import (
    DOPESHEET_MT_editor_menus,
    GRAPH_MT_editor_menus,
    NLA_MT_editor_menus,
    SEQUENCER_MT_editor_menus,
)
from bpy.app import version as BL_VERSION

from ..utils.logging import get_logger
from ..utils.ui_utils import ic

log = get_logger(__name__)

# TODO: チャンネル・Nパネルの同期対応
# C.space_data.show_region_channels
# C.space_data.show_region_ui


def draw_sync_visible_range(self, context):
    if not (context.space_data and hasattr(context.space_data, "show_locked_time")):
        return

    layout = self.layout

    sd = context.space_data
    lock_icon = "LOCKVIEW_ON" if sd.show_locked_time else "LOCKVIEW_OFF"

    layout.prop(sd, "show_locked_time", text="", icon=ic(lock_icon))
    layout.separator()


TIME_BASED_EDITOR_MENUS = [
    DOPESHEET_MT_editor_menus,
    GRAPH_MT_editor_menus,
    NLA_MT_editor_menus,
    SEQUENCER_MT_editor_menus,
]


def register():
    try:
        for menu in TIME_BASED_EDITOR_MENUS:
            menu.prepend(draw_sync_visible_range)
        if BL_VERSION >= (5, 0, 0):
            # ds_ctrl = getattr(__import__('bpy').types, "DOPESHEET_HT_playback_controls", None)
            # if ds_ctrl is not None:
            #     ds_ctrl.append(draw_sync_visible_range)
            pass
        else:
            time_menu = getattr(__import__("bpy").types, "TIME_MT_editor_menus", None)
            if time_menu is not None:
                time_menu.append(draw_sync_visible_range)
        log.debug("Sync visible range menus registered successfully")
    except Exception as e:
        log.error(f"Failed to register sync visible range menus: {e}")


def unregister():
    try:
        for menu in TIME_BASED_EDITOR_MENUS:
            menu.remove(draw_sync_visible_range)
        if BL_VERSION >= (5, 0, 0):
            ds_ctrl = getattr(
                __import__("bpy").types, "DOPESHEET_HT_playback_controls", None
            )
            if ds_ctrl is not None:
                try:
                    ds_ctrl.remove(draw_sync_visible_range)
                except Exception:
                    pass
        else:
            time_menu = getattr(__import__("bpy").types, "TIME_MT_editor_menus", None)
            if time_menu is not None:
                try:
                    time_menu.remove(draw_sync_visible_range)
                except Exception:
                    pass
        log.debug("Sync visible range menus unregistered successfully")
    except Exception as e:
        log.debug(f"Failed to unregister sync visible range menus: {e}")
