# pyright: reportInvalidTypeForm=false
import bpy
from rna_keymap_ui import draw_kmi

from .addon import ADDON_ID, get_prefs
from .keymap_manager import keymap_registry
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
            # self.draw_keymap(context, box)
            keymap_registry.draw_keymap_settings(context, box)

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
    def sync_logger_modules():
        """ロガーモジュールのインクリメンタル同期"""
        context = bpy.context
        try:
            pr = get_prefs(context)
            if not hasattr(pr, "logger_prefs"):
                return

            # 現在のロガーと設定済みモジュールを取得
            active_loggers = LoggerRegistry.get_all_loggers()
            existing_modules = {m.name for m in pr.logger_prefs.modules}

            # 新しいモジュールのみ追加（既存設定は保持）
            for module_name in active_loggers.keys():
                short_name = module_name
                if module_name.startswith(ADDON_ID + "."):
                    short_name = module_name[len(ADDON_ID) + 1 :]

                if short_name not in existing_modules:
                    pr.logger_prefs.register_module(short_name, "INFO")

            # 設定を適用
            pr.logger_prefs.update_logger_settings(context)

        except Exception as e:
            print(f"Logger sync error: {e}")

    bpy.app.timers.register(sync_logger_modules, first_interval=0.1)
