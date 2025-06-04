# bl_info = {
#     "name": "Playback Speed Controller",
#     "blender": (2, 80, 0),
#     "category": "Animation",
#     "version": (1, 0, 0),
#     "author": "Pluglug",
#     "description": "Control the playback speed of the animation",
# }

# Control the playback speed of the animation

import bpy
import bpy.app.handlers as handlers
from bpy.props import FloatProperty
from bpy.types import DOPESHEET_HT_header, Operator, Panel, Scene

from ..utils.ui_utils import ic

# 定数定義
DEFAULT_SPEED = 1.0
FRAME_MAP_BASE = 100
FRAME_MAP_MIN = 1
FRAME_MAP_MAX = 900
SPEED_TOLERANCE = 0.01

preset_items = [
    ("0.25", "¼x", ""),
    ("0.5", "½x", ""),
    ("1.0", "1x", ""),
    # ("1.5", "1.5x", ""),
    ("2.0", "2x", ""),
    # ("4.0", "4x", ""),
]


class PlaybackController:
    _instance = None
    _current_scene = None

    def __new__(cls, scene):
        if cls._instance is None or cls._current_scene != scene:
            cls._instance = super().__new__(cls)
            cls._current_scene = scene
        return cls._instance

    def __init__(self, scene):
        if (
            hasattr(self, "_initialized")
            and getattr(self, "_initialized", False)
            and getattr(self, "scene", None) == scene
        ):
            return

        self.scene = scene
        self._initialized = True

    def store_original_range(self):
        if (
            not hasattr(self.scene, "playback_speed")
            or abs(self.scene.playback_speed - DEFAULT_SPEED) > SPEED_TOLERANCE
        ):
            return

        self.scene["original_start"] = self.scene.frame_start
        self.scene["original_end"] = self.scene.frame_end

    def adjust_range(self, frame_map_old, frame_map_new):
        # original値が存在しない場合は現在の値を使用
        original_start = self.scene.get("original_start", self.scene.frame_start)
        original_end = self.scene.get("original_end", self.scene.frame_end)

        ratio = frame_map_new / frame_map_old
        new_start = round(original_start * ratio)
        new_end = round(original_end * ratio)

        self.scene.frame_start = new_start
        self.scene.frame_end = new_end

    def apply_speed(self, playback_speed):
        playback_speed = round(playback_speed, 2)
        frame_map_old = round(playback_speed * FRAME_MAP_BASE)
        frame_map_old = max(FRAME_MAP_MIN, min(FRAME_MAP_MAX, frame_map_old))

        self.scene.render.frame_map_old = frame_map_old
        self.scene.render.frame_map_new = FRAME_MAP_BASE

        self.adjust_range(frame_map_old, self.scene.render.frame_map_new)

    @classmethod
    def get_instance(cls, scene):
        return cls(scene)


class SCENE_OT_store_original_range(Operator):
    bl_idname = "scene.store_original_range"
    bl_label = "Store Original Playback Range"
    bl_description = (
        "Store the original playback range before applying playback speed adjustments"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        controller = PlaybackController.get_instance(context.scene)

        if not hasattr(context.scene, "playback_speed"):
            self.report({"ERROR"}, "Playback speed is not set")
            return {"CANCELLED"}

        # 速度変化中の保存を防ぐ安全策
        if abs(context.scene.playback_speed - DEFAULT_SPEED) > SPEED_TOLERANCE:
            self.report(
                {"WARNING"},
                f"速度変化中（{context.scene.playback_speed:.2f}x）はオリジナル範囲保存不可。"
                "まず速度を1.0xにリセットしてください。",
            )
            return {"CANCELLED"}

        context.scene.playback_speed = 1.0
        controller.store_original_range()
        return {"FINISHED"}


class SCENE_OT_reset_speed(Operator):
    bl_idname = "scene.reset_speed"
    bl_label = "Reset Playback Speed"
    bl_description = "Reset playback speed and return to original playback range"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # playback_speedを設定することで、on_speed_updateが自動的に呼ばれ
        # controller.apply_speed()とフレーム範囲調整が適切に実行される
        context.scene.playback_speed = 1.0
        return {"FINISHED"}


class SCENE_OT_set_playback_speed_preset(Operator):
    bl_idname = "scene.set_playback_speed_preset"
    bl_label = "Set Playback Speed Preset"
    bl_description = "Set playback speed to preset value"
    bl_options = {"REGISTER", "UNDO"}

    speed: FloatProperty(
        name="Speed",
        description="Playback speed value",
        default=1.0,
    )

    def execute(self, context):
        context.scene.playback_speed = self.speed
        return {"FINISHED"}


class SCENE_OT_save_custom_preset(Operator):
    bl_idname = "scene.save_custom_preset"
    bl_label = "Save Custom Speed Preset"
    bl_description = "Save current speed as custom preset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        speed = context.scene.playback_speed
        # カスタムプリセットをシーンプロパティに保存
        if "custom_speed_presets" not in context.scene:
            context.scene["custom_speed_presets"] = []

        presets = list(context.scene.get("custom_speed_presets", []))
        if speed not in presets and speed != 1.0:  # 1.0は既にデフォルトで存在
            presets.append(speed)
            presets.sort()
            context.scene["custom_speed_presets"] = presets
            self.report({"INFO"}, f"カスタムプリセット {speed:.2f}x を保存しました")
        else:
            self.report({"WARNING"}, "このプリセットは既に存在します")

        return {"FINISHED"}


def on_speed_update(scene, context):
    controller = PlaybackController.get_instance(scene)
    controller.apply_speed(scene.playback_speed)


def draw_ui(self, context):
    layout = self.layout
    scene = context.scene

    # ヘッダー用の1行レイアウト
    row = layout.row(align=True)

    # 速度スライダー
    col = row.column(align=True)
    col.prop(scene, "playback_speed", text="", icon=ic("MOD_TIME"))

    # プリセットボタン
    col = row.column(align=True)
    col.scale_x = 0.5
    preset_row = col.row(align=True)
    for speed_value, speed_label, _ in preset_items:
        op = preset_row.operator("scene.set_playback_speed_preset", text=speed_label)
        op.speed = float(speed_value)

    # 制御ボタン
    row.separator()
    col = row.column(align=True)
    control_row = col.row(align=True)

    # ストアボタン - 速度変化を考慮した判定
    def get_store_button_state(scene):
        # original値の存在確認
        original_start = scene.get("original_start")
        original_end = scene.get("original_end")

        # 現在の速度状態をチェック
        is_speed_normal = abs(scene.playback_speed - DEFAULT_SPEED) <= SPEED_TOLERANCE

        # 速度変化中の場合
        if not is_speed_normal:
            if original_start is not None and original_end is not None:
                # オリジナル保存済み + 速度変化中 = 正常利用中（青・無効）
                return "using", True  # (state, enabled)
            else:
                # オリジナル未保存 + 速度変化中 = 警告（赤・無効）
                return "warning", False

        # 速度が通常時（1.0x）の場合
        if original_start is None or original_end is None:
            # 未保存（赤・有効）
            return "need_save", True

        # 現在の範囲とoriginal範囲を比較
        current_start = scene.frame_start
        current_end = scene.frame_end

        start_changed = abs(int(original_start) - current_start) > 0
        end_changed = abs(int(original_end) - current_end) > 0

        if start_changed or end_changed:
            # 変更あり（赤・有効）
            return "need_update", True
        else:
            # 保存済み・変更なし（緑・有効）
            return "saved", True

    button_state, button_enabled = get_store_button_state(scene)

    # アイコンの決定
    if button_state == "using":
        store_icon = ic("SEQUENCE_COLOR_05")  # Blue - オリジナル範囲利用中
    elif button_state == "warning":
        store_icon = ic("SEQUENCE_COLOR_01")  # Red - 速度変化中だが未保存
    elif button_state == "need_save" or button_state == "need_update":
        store_icon = ic("SEQUENCE_COLOR_01")  # Red - 保存/更新が必要
    else:  # saved
        store_icon = ic("SEQUENCE_COLOR_04")  # Green - 保存済み・問題なし

    store_op = control_row.operator(
        "scene.store_original_range", text="", icon=store_icon
    )

    # 速度変化中の場合は視覚的にも分かりやすくする
    if not button_enabled:
        # 無効状態を視覚的に示すため、アルファ値を下げる
        # Blenderでは直接的な無効化が難しいため、視覚的フィードバックで対応
        pass  # 現在は視覚的な区別のみ

    # リセットボタン
    if scene.playback_speed != 1.00:
        reset_icon = ic("CANCEL")
    else:
        reset_icon = ic("PLAY")

    control_row.operator("scene.reset_speed", text="", icon=reset_icon)


def store_range_on_load(dummy):
    controller = PlaybackController.get_instance(bpy.context.scene)
    controller.store_original_range()
    controller.apply_speed(bpy.context.scene.playback_speed)


def register():
    Scene.playback_speed = FloatProperty(
        name="Playback Speed",
        description="Control the playback speed of the animation",
        default=1.0,
        min=0.01,
        max=9.0,
        soft_min=0.1,
        soft_max=2.0,
        step=10,
        precision=2,
        update=on_speed_update,
        subtype="FACTOR",
    )

    DOPESHEET_HT_header.append(draw_ui)
    handlers.load_post.append(store_range_on_load)


def unregister():
    if hasattr(Scene, "playback_speed"):
        bpy.context.scene.playback_speed = 1.0

    DOPESHEET_HT_header.remove(draw_ui)
    handlers.load_post.remove(store_range_on_load)

    del Scene.playback_speed
