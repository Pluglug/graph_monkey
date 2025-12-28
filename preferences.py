# pyright: reportInvalidTypeForm=false
from bpy.props import BoolProperty, EnumProperty, PointerProperty
from bpy.types import AddonPreferences

from .addon import ADDON_ID, get_prefs
from .keymap_manager import keymap_registry
from .operators.channel_selection_overlay import ChannelSelectionOverlaySettings
# TODO: Rename to pose_transform_visualizer
from .operators.pose_rotation_visualizer import PoseTransformVisualizerSettings
from .ui.playback_preview import PlaybackPreviewSettings

# from .ui.calculator.preferences import CalculatorPreferences
from .utils.logger_prefs import MONKEY_LoggerPreferences
from .utils.logging import LoggerRegistry, get_logger

# from .utils.ui_utils import draw_multiline_text_examples

# log = get_logger(__name__)


class MonKeyPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    tab: EnumProperty(
        name="Tab",
        description="Tab to open",
        items=[
            ("HowToUse", "How to use", ""),
            # ("CALCULATOR", "Calculator", ""),
            ("KEYMAP", "Keymap", ""),
            ("GRAPH_EDITOR", "Graph Editor", ""),
            ("OVERLAY", "Overlay", ""),
            ("POSE_VISUALIZER", "Pose Visualizer", ""),
            ("PLAYBACK", "Playback", ""),
        ],
        default="HowToUse",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # Graph Editor Options
    auto_focus_on_channel_change: BoolProperty(
        name="Auto Focus on Channel Change",
        description="チャンネル移動（Monkey Vertically）実行後、選択カーブにフォーカスする",
        default=True,
    )
    # calculator: PointerProperty(type=CalculatorPreferences)
    overlay: PointerProperty(type=ChannelSelectionOverlaySettings)
    pose_visualizer: PointerProperty(type=PoseTransformVisualizerSettings)
    logger_prefs: PointerProperty(type=MONKEY_LoggerPreferences)
    playback_preview: PointerProperty(type=PlaybackPreviewSettings)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tab", expand=True)

        box = layout.box()
        if self.tab == "HowToUse":
            self.draw_description(context, box)
        # elif self.tab == "CALCULATOR":
        #     self.calculator.draw(context, box)
        elif self.tab == "GRAPH_EDITOR":
            self.draw_graph_editor_settings(context, box)
        elif self.tab == "OVERLAY":
            self.overlay.draw(context, box)
        elif self.tab == "POSE_VISUALIZER":
            self.pose_visualizer.draw(context, box)
        elif self.tab == "KEYMAP":
            keymap_registry.draw_keymap_settings(context, box)
        elif self.tab == "PLAYBACK":
            self.playback_preview.draw(context, box)

    def draw_description(self, context, layout):
        layout.label(text="TODO: Add description")
        # draw_multiline_text_examples(layout)

        MONKEY_LoggerPreferences.draw(self.logger_prefs, layout)

    def draw_graph_editor_settings(self, context, layout):
        col = layout.column()
        col.label(text="Monkey Vertically (チャンネル移動)")
        col.prop(self, "auto_focus_on_channel_change")


def register():
    import bpy

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
