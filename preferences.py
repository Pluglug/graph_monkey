# pyright: reportInvalidTypeForm=false
import bpy
from rna_keymap_ui import draw_kmi

from .addon import ADDON_ID, get_prefs
from .operators.handle_selection import GRAPH_OT_monkey_handle_selecter
from .operators.keyframe_selection import (
    GRAPH_OT_monkey_horizontally,
    GRAPH_OT_monkey_vertically,
)
from .operators.channel_selection_overlay import ChannelSelectionOverlaySettings
from .utils.logger_prefs import MONKEY_LoggerPreferences
from .utils.logging import LoggerRegistry, get_logger

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
    overlay: bpy.props.PointerProperty(type=ChannelSelectionOverlaySettings)
    logger_prefs: bpy.props.PointerProperty(type=MONKEY_LoggerPreferences)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tab", expand=True)

        box = layout.box()
        if self.tab == "HowToUse":
            self.draw_description(context, box)
        elif self.tab == "OVERLAY":
            self.overlay.draw(context, box)
        elif self.tab == "KEYMAP":
            self.draw_keymap(context, box)

    def draw_description(self, context, layout):
        layout.label(text="TODO: Add description")

        MONKEY_LoggerPreferences.draw(self.logger_prefs, layout)

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


def register():

    context = bpy.context
    pr = get_prefs(context)
    if hasattr(pr, "logger_prefs"):
        mods = LoggerRegistry.get_all_loggers()
        current_module_names = {m.name for m in pr.logger_prefs.modules}
        for module_name, _logger in mods.items():
            if module_name not in current_module_names:
                pr.logger_prefs.register_module(module_name, "INFO")
        # 設定の更新もここで呼び出すのが適切か？
        # for module in pr.logger_prefs.modules:
        #     module.log_level = "DEBUG"
        pr.logger_prefs.update_logger_settings(context)
