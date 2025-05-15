# pyright: reportInvalidTypeForm=false
import bpy
from rna_keymap_ui import draw_kmi

from .utils.logging import get_logger
from .utils.logger_prefs import MonKeyLoggerPrefs

from .addon import ADDON_ID

from .operators.keyframe_moving import (
    GRAPH_OT_monkey_horizontally,
    GRAPH_OT_monkey_vertically,
)
from .operators.handle_selection import GRAPH_OT_monkey_handle_selecter

from .overlay import TextOverlaySettings, ChannelInfoToDisplay

ops_idnames = [
    GRAPH_OT_monkey_horizontally.bl_idname,
    GRAPH_OT_monkey_vertically.bl_idname,
    GRAPH_OT_monkey_handle_selecter.bl_idname,
]

log = get_logger(__name__)


class MonKeyPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    tab: bpy.props.EnumProperty(
        name="Tab",
        description="Tab to open",
        items=[
            ("HowToUse", "How to use", ""),
            ("KEYMAP", "Keymap", ""),
            ("OVERLAY", "Overlay", ""),
        ],
        default="HowToUse",
    )
    overlay: bpy.props.PointerProperty(type=TextOverlaySettings)
    info_to_display: bpy.props.PointerProperty(type=ChannelInfoToDisplay)

    # debug_flags: bpy.props.PointerProperty(type=DebugFlagsGroup)
    logger_prefs: bpy.props.PointerProperty(type=MonKeyLoggerPrefs)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tab", expand=True)

        box = layout.box()
        if self.tab == "HowToUse":
            self.draw_description(context, box)
        elif self.tab == "OVERLAY":
            self.overlay.draw(context, box)
            box.separator()
            self.info_to_display.draw(context, box)
        elif self.tab == "KEYMAP":
            self.draw_keymap(context, box)

    def draw_description(self, context, layout):
        layout.label(text="TODO: Add description")

        MonKeyLoggerPrefs.draw(self.logger_prefs, layout)

    def draw_keymap(self, context, layout):
        wm = context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps.get("Graph Editor")

        if not km:
            return

        layout.label(text="MonKey Keymap")

        for kmi in km.keymap_items:
            if kmi.idname in ops_idnames:
                draw_kmi([], kc, km, kmi, layout, 0)


# del ops_idnames
# del GRAPH_OT_monkey_horizontally
# del GRAPH_OT_monkey_vertically
# del GRAPH_OT_monkey_handle_selecter
