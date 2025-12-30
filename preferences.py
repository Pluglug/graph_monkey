# pyright: reportInvalidTypeForm=false
from bpy.props import BoolProperty, EnumProperty, PointerProperty
from bpy.types import AddonPreferences

from .addon import ADDON_ID, get_prefs
from .keymap_manager import keymap_registry
from .operators.channel_navigator import ChannelNavigatorSettings
from .operators.channel_selection_overlay import ChannelSelectionOverlaySettings
# TODO: Rename to pose_transform_visualizer
from .operators.pose_rotation_visualizer import PoseTransformVisualizerSettings
from .ui.playback_preview import PlaybackPreviewSettings
from .utils.i18n import _
from .utils.ui_utils import ic, ui_multiline_text

# ロガー設定（開発用・通常は非表示）
# from .utils.logger_prefs import MONKEY_LoggerPreferences
# from .utils.logging import LoggerRegistry, get_logger


class MonKeyPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    tab: EnumProperty(
        name="Tab",
        description="Tab to open",
        items=[
            ("HOW_TO_USE", "How to use", ""),
            ("SETTINGS", "Settings", ""),
            ("KEYMAP", "Keymap", ""),
        ],
        default="HOW_TO_USE",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # Graph Editor Options
    auto_focus_on_channel_change: BoolProperty(
        name="Auto Focus on Channel Change",
        description="Automatically focus on selected curve when changing channels",
        default=True,
    )
    auto_follow_current_frame: BoolProperty(
        name="Auto Follow Current Frame",
        description="Move current frame when selecting a single keyframe",
        default=False,
    )

    channel_navigator: PointerProperty(type=ChannelNavigatorSettings)
    overlay: PointerProperty(type=ChannelSelectionOverlaySettings)
    pose_visualizer: PointerProperty(type=PoseTransformVisualizerSettings)
    playback_preview: PointerProperty(type=PlaybackPreviewSettings)
    # logger_prefs: PointerProperty(type=MONKEY_LoggerPreferences)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tab", expand=True)

        box = layout.box()
        if self.tab == "HOW_TO_USE":
            self.draw_description(context, box)
        elif self.tab == "SETTINGS":
            self.draw_settings(context, box)
        elif self.tab == "KEYMAP":
            keymap_registry.draw_keymap_settings(context, box)

    def draw_description(self, context, layout):
        # Addon description
        ui_multiline_text(layout, _("ADDON_DESC"), icon=ic("INFO"))
        # layout.separator()

        # Quick Start
        col = layout.column()
        col.label(text=_("QUICK_START"), icon=ic("PLAY"))
        box = col.box()
        box.label(text=_("WASD_QUICK"), icon=ic("EVENT_W"))
        box.label(text=_("NUM_QUICK"), icon=ic("EVENT_ONEKEY"))
        box.label(text=_("NAV_QUICK"), icon=ic("EVENT_Y"))
        box.label(text=_("PIE_QUICK"), icon=ic("EVENT_T"))

        # layout.separator()

        # Features
        col = layout.column()
        col.label(text=_("FEATURES"), icon=ic("COLLAPSEMENU"))
        box = col.box()
        box.label(text=_("FEATURE_WASD"))
        box.label(text=_("FEATURE_NAVIGATOR"))
        box.label(text=_("FEATURE_PEEK"))
        box.label(text=_("FEATURE_PIE"))
        box.label(text=_("FEATURE_PLAYBACK"))
        box.label(text=_("FEATURE_VISUALIZER"))

        # layout.separator()

        # GitHub link
        row = layout.row()
        row.operator(
            "wm.url_open",
            text=_("DOC_LINK"),
            icon=ic("URL"),
        ).url = _("GITHUB_URL")

    def draw_settings(self, context, layout):
        # Graph Editor
        box = layout.box()
        box.label(text=_("GRAPH_EDITOR_SETTINGS"), icon=ic("GRAPH"))
        col = box.column()
        col.label(text=_("CHANNEL_MOVE"))
        col.prop(self, "auto_focus_on_channel_change")
        col.separator()
        col.label(text=_("KEYFRAME_MOVE"))
        col.prop(self, "auto_follow_current_frame")

        # Channel Navigator
        box = layout.box()
        box.label(text=_("CHANNEL_NAV_SETTINGS"), icon=ic("OUTLINER"))
        self.channel_navigator.draw(context, box)

        # Channel Overlay
        box = layout.box()
        box.label(text=_("OVERLAY_SETTINGS"), icon=ic("OVERLAY"))
        self.overlay.draw(context, box)

        # Pose Visualizer
        box = layout.box()
        box.label(text=_("POSE_VISUALIZER_SETTINGS"), icon=ic("POSE_HLT"))
        self.pose_visualizer.draw(context, box)

        # Playback Preview
        box = layout.box()
        box.label(text=_("PLAYBACK_SETTINGS"), icon=ic("PLAY"))
        self.playback_preview.draw(context, box)

def register():
    pass
    # ロガー設定の同期（開発用・通常はコメントアウト）
    # import bpy
    # def sync_logger_modules():
    #     """ロガーモジュールのインクリメンタル同期"""
    #     context = bpy.context
    #     try:
    #         pr = get_prefs(context)
    #         if not hasattr(pr, "logger_prefs"):
    #             return
    #         active_loggers = LoggerRegistry.get_all_loggers()
    #         existing_modules = {m.name for m in pr.logger_prefs.modules}
    #         for module_name in active_loggers.keys():
    #             short_name = module_name
    #             if module_name.startswith(ADDON_ID + "."):
    #                 short_name = module_name[len(ADDON_ID) + 1 :]
    #             if short_name not in existing_modules:
    #                 pr.logger_prefs.register_module(short_name, "INFO")
    #         pr.logger_prefs.update_logger_settings(context)
    #     except Exception as e:
    #         print(f"Logger sync error: {e}")
    # bpy.app.timers.register(sync_logger_modules, first_interval=0.1)
