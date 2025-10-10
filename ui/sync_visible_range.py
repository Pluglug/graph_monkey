from bpy.types import (
    DOPESHEET_MT_editor_menus,
    GRAPH_MT_editor_menus,
    NLA_MT_editor_menus,
    SEQUENCER_MT_editor_menus,
    TIME_MT_editor_menus,
)

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
    TIME_MT_editor_menus,
]


def register():
    try:
        for menu in TIME_BASED_EDITOR_MENUS:
            menu.prepend(draw_sync_visible_range)
        log.debug("Sync visible range menus registered successfully")
    except Exception as e:
        log.error(f"Failed to register sync visible range menus: {e}")


def unregister():
    try:
        for menu in TIME_BASED_EDITOR_MENUS:
            menu.remove(draw_sync_visible_range)
        log.debug("Sync visible range menus unregistered successfully")
    except Exception as e:
        log.debug(f"Failed to unregister sync visible range menus: {e}")
