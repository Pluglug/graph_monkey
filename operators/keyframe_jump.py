import bpy
from bpy.types import Operator, Context, Area
from bpy.props import BoolProperty, StringProperty

from ..utils.logging import get_logger
from ..keymap.keymap_manager import KeymapDefinition, keymap_registry

log = get_logger(__name__)


class MONKEY_OT_JUMP_WITHIN_RANGE(Operator):
    bl_idname = "keyframe.jump_within_range"
    bl_label = "Jump within range"
    bl_description = "Jump within range"
    bl_options = set()

    next: BoolProperty(default=True, options={"SKIP_SAVE"})
    loop: BoolProperty(default=True, options={"SKIP_SAVE"})
    called_from: StringProperty(default="", options={"SKIP_SAVE"})

    def execute(self, context: Context):
        log.debug(f"Called from: {self.called_from}")

        # フレーム範囲を設定
        self._setup_frame_range(context)

        # メインのジャンプ処理を実行
        return self.jump_within_range(context)

    # ===========================================
    # メインのジャンプ処理
    # ===========================================

    def jump_within_range(self, context: Context):
        """範囲内でのキーフレームジャンプのメイン処理"""
        scene = context.scene
        current_frame = scene.frame_current

        # 1. キーフレームジャンプを実行
        if not self._execute_keyframe_jump(context):
            return {"FINISHED"}

        # 2. ジャンプ後の状態をチェック
        new_frame = scene.frame_current
        out_of_range = new_frame < self.start_frame or new_frame > self.end_frame
        did_not_move = new_frame == current_frame

        # 3. 範囲外または動かなかった場合のループ処理
        if (did_not_move or out_of_range) and self.loop:
            self._handle_loop_jump(context)

        return {"FINISHED"}

    # ===========================================
    # ヘルパーメソッド（実行順序）
    # ===========================================

    def _setup_frame_range(self, context: Context):
        """フレーム範囲の設定"""
        scene = context.scene
        if scene.use_preview_range:
            self.start_frame = scene.frame_preview_start
            self.end_frame = scene.frame_preview_end
        else:
            self.start_frame = scene.frame_start
            self.end_frame = scene.frame_end

    def _execute_keyframe_jump(self, context: Context) -> bool:
        """キーフレームジャンプの実行（エラーハンドリング付き）"""
        try:
            bpy.ops.screen.keyframe_jump(next=self.next)
            return True
        except RuntimeError as e:
            log.warning(f"keyframe_jump failed in {context.area.ui_type}: {e}")
            # フォールバック: 通常のフレーム移動
            if self.next:
                bpy.ops.screen.frame_offset(delta=1)
            else:
                bpy.ops.screen.frame_offset(delta=-1)
            return False

    def _handle_loop_jump(self, context: Context):
        """ループ処理：範囲の逆端に移動してキーフレームをチェック"""
        scene = context.scene

        # 逆端に移動
        if self.next:
            scene.frame_set(self.start_frame)
        else:
            scene.frame_set(self.end_frame)

        # 逆端に可視キーフレームがあれば終了
        if self._has_visible_keyframe_at_current_frame(context):
            return

        # なければもう一度ジャンプ
        self._execute_keyframe_jump(context)

    # ===========================================
    # キーフレーム検出メソッド
    # ===========================================

    def _has_visible_keyframe_at_current_frame(self, context: Context) -> bool:
        """
        現在のフレームに可視キーフレームがあるかチェック
        必要に応じてTIMELINEコンテキストに切り替える
        """
        # 1. 現在のコンテキストで試す
        if self._check_visible_fcurves(context):
            return self._check_keyframe_at_frame(context)

        # 2. TIMELINEエリアで試す
        timeline_area = self._find_timeline_area(context)
        if timeline_area:
            with context.temp_override(area=timeline_area):
                if self._check_visible_fcurves(context):
                    return self._check_keyframe_at_frame(context)

        # 3. 他のアニメーションエリアで試す
        return self._try_animation_areas(context)

    def _check_visible_fcurves(self, context: Context) -> bool:
        """visible_fcurvesが利用可能かチェック"""
        return hasattr(context, "visible_fcurves") and context.visible_fcurves

    def _check_keyframe_at_frame(self, context: Context) -> bool:
        """現在のフレームにキーフレームがあるかチェック"""
        scene = context.scene
        current_frame = scene.frame_current

        visible_fcurves = getattr(context, "visible_fcurves", None)
        if not visible_fcurves:
            return False

        for fcurve in visible_fcurves:
            for kp in fcurve.keyframe_points:
                if int(kp.co.x) == current_frame:
                    return True
        return False

    def _try_animation_areas(self, context: Context) -> bool:
        """他のアニメーションエリアでvisible_fcurvesを試す"""
        animation_areas = ["DOPESHEET_EDITOR", "GRAPH_EDITOR", "NLA_EDITOR"]
        for area_type in animation_areas:
            for area in context.window.screen.areas:
                if area.type == area_type:
                    with context.temp_override(area=area):
                        if self._check_visible_fcurves(context):
                            return self._check_keyframe_at_frame(context)
        return False

    # ===========================================
    # ユーティリティメソッド
    # ===========================================

    @staticmethod
    def _find_timeline_area(context: Context) -> Area | None:
        """TIMELINEエリアを探す"""
        for area in context.window.screen.areas:
            if area.ui_type == "TIMELINE":
                return area
        return None

    # ===========================================
    # 旧メソッド（互換性のため残す）
    # ===========================================

    @staticmethod
    def visible_key_on_current_frame(context: Context) -> bool:
        """
        【非推奨】現在のフレーム位置に可視状態のキーフレームがあればTrue
        新しいコードでは _has_visible_keyframe_at_current_frame を使用してください
        """
        scene = context.scene
        current_frame = scene.frame_current

        visible_fcurves = getattr(context, "visible_fcurves", None)
        if not visible_fcurves:
            return False

        for fcurve in visible_fcurves:
            for kp in fcurve.keyframe_points:
                if int(kp.co.x) == current_frame:
                    return True
        return False


class MONKEY_OT_KEYFRAME_PEEK(Operator):
    bl_idname = "keyframe.peek_next"
    bl_label = "Peek Next Keyframe"
    bl_description = (
        "Peek next/previous keyframe while key is held down, return to original frame when released. "
        "Ctrl key to stay at the destination frame. "
    )

    next: BoolProperty(default=True, options={"SKIP_SAVE"})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_frame = None
        self.peek_key_type = None

    def modal(self, context, event):
        # 押されたキーと同じキーが離されたかを判定
        if event.type == self.peek_key_type and event.value == "RELEASE":
            # Ctrlキーが押されている場合は、現在のフレームにとどまって終了
            if event.ctrl:
                # 移動先にとどまる（original_frameには戻らない）
                self.original_frame = None
                return {"FINISHED"}

            # 通常の場合は元のフレームに戻る
            if self.original_frame is not None:
                context.scene.frame_set(self.original_frame)
                self.original_frame = None
            return {"FINISHED"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        # キータイプを設定
        self.peek_key_type = event.type

        # 元のフレームを記憶
        self.original_frame = context.scene.frame_current

        # タイムラインエリアを探す
        timeline_area = MONKEY_OT_JUMP_WITHIN_RANGE.find_area_with_visible_fcurves(
            context
        )

        if timeline_area:
            with context.temp_override(area=timeline_area):
                # 次のキーフレームへジャンプ
                bpy.ops.screen.keyframe_jump(next=self.next)
        else:
            # タイムラインエリアがない場合は通常ジャンプ
            bpy.ops.screen.keyframe_jump(next=self.next)

        # モーダル開始
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


KEYFRAME_JUMP_KEYMAPS = [
    ("Dopesheet", "DOPESHEET_EDITOR"),
    ("Frames", "EMPTY"),
    ("Graph Editor", "GRAPH_EDITOR"),
    ("Object Mode", "EMPTY"),
    ("Pose", "EMPTY"),
]

keymap_definitions = []

for keymap_name, keymap_space_type in KEYFRAME_JUMP_KEYMAPS:
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="screen.frame_offset",  # Built-in operator
            key="ONE",
            value="PRESS",
            repeat=True,
            properties={"delta": -1},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="screen.frame_offset",  # Built-in operator
            key="TWO",
            value="PRESS",
            repeat=True,
            properties={"delta": 1},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.jump_within_range",
            key="THREE",
            value="PRESS",
            repeat=True,
            properties={"next": False, "loop": True, "called_from": keymap_name},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.jump_within_range",
            key="FOUR",
            value="PRESS",
            repeat=True,
            properties={"next": True, "loop": True, "called_from": keymap_name},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.peek_next",
            key="THREE",
            shift=True,
            value="PRESS",
            repeat=False,
            properties={"next": False},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.peek_next",
            key="FOUR",
            shift=True,
            value="PRESS",
            repeat=False,
            properties={"next": True},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )

keymap_registry.register_keymap_group("Keyframe Jump", keymap_definitions)


# def register():
#     bpy.types.Scene.keyframe_jump_wrap = BoolProperty(
#         name="Loop Keyframe Jump",
#         description="Loop keyframe jump within frame range",
#         default=True,
#     )
# def unregister():
#     del bpy.types.Scene.keyframe_jump_wrap
