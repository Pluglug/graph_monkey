# pyright: reportInvalidTypeForm=false
import bpy
from bpy.types import Operator, Context
from bpy.props import BoolProperty, StringProperty, EnumProperty

from ..utils.logging import get_logger
from ..keymap_manager import KeymapDefinition, keymap_registry
from ..utils.anim_utils import (
    select_target_frame_from_list,
    find_timeline_area,
    get_allowed_frames_in_range_cached,
    invalidate_allowed_frames_cache,
)
from ..constants import KEYFRAME_TYPE_FLAGS


log = get_logger(__name__)


def keyframe_jump_in_timeline(context: Context, go_next: bool) -> None:
    """タイムラインの可視キー基準でキーフレームジャンプを実行する小ヘルパー。"""
    timeline_area = find_timeline_area(context)
    if timeline_area:
        with context.temp_override(area=timeline_area):
            bpy.ops.screen.keyframe_jump(next=go_next)
    else:
        bpy.ops.screen.keyframe_jump(next=go_next)


class MONKEY_OT_JUMP_WITHIN_RANGE(Operator):
    bl_idname = "keyframe.jump_within_range"
    bl_label = "Jump within range"
    bl_description = "Jump within range"
    bl_options = set()

    next: BoolProperty(default=True, options={"SKIP_SAVE"})
    loop: BoolProperty(default=True, options={"SKIP_SAVE"})
    called_from: StringProperty(default="", options={"SKIP_SAVE"})  # debug
    start_frame: int = 0
    end_frame: int = 0

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
        """キーフレームジャンプの実行（フィルタ有りは直接ターゲットへ、無しは通常ジャンプ）"""
        scene = context.scene
        allowed_types = self._parse_allowed_key_types(context)

        # フィルタ未指定: 既存のBlenderオペレーターに委譲
        if not allowed_types:
            try:
                # View3Dからでもタイムラインの可視キー基準でジャンプさせる
                keyframe_jump_in_timeline(context, self.next)
                return True
            except RuntimeError as e:
                log.warning(f"keyframe_jump failed in {context.area.ui_type}: {e}")
                if self.next:
                    bpy.ops.screen.frame_offset(delta=1)
                else:
                    bpy.ops.screen.frame_offset(delta=-1)
                return False

        # フィルタ指定: 可視Fカーブから許可タイプのフレームを抽出して直接移動
        allowed_frames = get_allowed_frames_in_range_cached(
            context,
            self.start_frame,
            self.end_frame,
            allowed_types,
        )
        if not allowed_frames:
            return True

        current = scene.frame_current
        target = select_target_frame_from_list(
            allowed_frames, current, self.next, self.loop
        )
        if target is None:
            return True

        scene.frame_set(target)
        return True

    def _handle_loop_jump(self, context: Context):
        """ループ処理：範囲の逆端に移動してキーフレームをチェック"""
        scene = context.scene
        allowed_types = self._parse_allowed_key_types(context)

        # フィルタ未指定: 従来動作（端へ移動→通常ジャンプ）
        if not allowed_types:
            if self.next:
                scene.frame_set(self.start_frame)
            else:
                scene.frame_set(self.end_frame)
            if self._has_visible_keyframe_at_current_frame(context, None):
                return
            self._execute_keyframe_jump(context)
            return

        # フィルタ指定: 端に寄せず、リストから直接選択（先頭/末尾）
        allowed_frames = get_allowed_frames_in_range_cached(
            context,
            self.start_frame,
            self.end_frame,
            allowed_types,
        )
        if not allowed_frames:
            return
        if self.next:
            scene.frame_set(allowed_frames[0])
        else:
            scene.frame_set(allowed_frames[-1])

    # ===========================================
    # キーフレーム検出メソッド
    # ===========================================

    def _has_visible_keyframe_at_current_frame(
        self, context: Context, allowed_types: set[str] | None = None
    ) -> bool:
        """
        現在のフレームに可視キーフレームがあるかチェック
        必要に応じてTIMELINEコンテキストに切り替える
        """
        # 1. 現在のコンテキストで試す
        if self._check_visible_fcurves(context):
            return self._check_keyframe_at_frame(context, allowed_types)

        # 2. TIMELINEエリアで試す
        timeline_area = find_timeline_area(context)
        if timeline_area:
            with context.temp_override(area=timeline_area):
                if self._check_visible_fcurves(context):
                    return self._check_keyframe_at_frame(context, allowed_types)

        # 3. 他のアニメーションエリアで試す
        return self._try_animation_areas(context, allowed_types)

    def _check_visible_fcurves(self, context: Context) -> bool:
        """visible_fcurvesが利用可能かチェック"""
        return hasattr(context, "visible_fcurves") and context.visible_fcurves

    def _check_keyframe_at_frame(
        self, context: Context, allowed_types: set[str] | None = None
    ) -> bool:
        """現在のフレームにキーフレームがあるかチェック"""
        scene = context.scene
        current_frame = scene.frame_current

        visible_fcurves = getattr(context, "visible_fcurves", None)
        if not visible_fcurves:
            return False

        for fcurve in visible_fcurves:
            for kp in fcurve.keyframe_points:
                if int(kp.co.x) == current_frame:
                    if not allowed_types or getattr(kp, "type", None) in allowed_types:
                        return True
        return False

    def _try_animation_areas(
        self, context: Context, allowed_types: set[str] | None = None
    ) -> bool:
        """他のアニメーションエリアでvisible_fcurvesを試す"""
        animation_areas = ["DOPESHEET_EDITOR", "GRAPH_EDITOR", "NLA_EDITOR"]
        for area_type in animation_areas:
            for area in context.window.screen.areas:
                if area.type == area_type:
                    with context.temp_override(area=area):
                        if self._check_visible_fcurves(context):
                            return self._check_keyframe_at_frame(context, allowed_types)
        return False

    # ===========================================
    # キーフレームタイプ フィルタ ユーティリティ
    # ===========================================

    def _parse_allowed_key_types(self, context: Context) -> set[str]:
        """シーンのフラグ型Enumから選択タイプ集合を返す。未選択なら空集合（=全許可）。"""
        value = getattr(context.scene, "monkey_keyframe_filter_type", None)
        # BlenderのENUM_FLAGは set[str] になる。未定義/空はフィルタなし。
        if not value:
            return set()
        if isinstance(value, str):
            return {value.upper()}
        try:
            return {str(v).upper() for v in value}
        except Exception:
            return set()

    # ===========================================
    # タイムライン メニュー UI
    # ===========================================


def draw_timeline_filter_menu(menu, context: Context):
    layout = menu.layout
    layout.separator()
    layout.prop(context.scene, "monkey_keyframe_filter_type", icon_only=True)
    layout.separator()


class MONKEY_OT_KEYFRAME_PEEK(Operator):
    bl_idname = "keyframe.peek_next"
    bl_label = "Peek Next Keyframe"
    bl_description = (
        "Peek next/previous keyframe while key is held down, return to original frame when released. "
        "Ctrl key to stay at the destination frame. "
        "1/2 keys to offset by additional frames. Q to reset to original position."
    )

    next: BoolProperty(default=True, options={"SKIP_SAVE"})

    # クラス変数でオフセット状態を保持（方向別）
    _offset_frames_next = 0  # 前方向のオフセット
    _offset_frames_prev = 0  # 後方向のオフセット

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_frame = None
        self.peek_key_type = None
        self.current_offset = 0
        self.stay_on_release = False

    def modal(self, context, event):
        # Shiftが離されたら、最終的に移動先にとどまるフラグを立てて、peekキーが離されるまで維持
        if event.type in {"LEFT_SHIFT", "RIGHT_SHIFT"} and event.value == "RELEASE":
            self.stay_on_release = True
            return {"RUNNING_MODAL"}
        # 押されたキーと同じキーが離されたかを判定
        if event.type == self.peek_key_type and event.value == "RELEASE":
            # Shiftが離されたことがある、または現在Shiftが押されていない場合は滞在
            should_stay = self.stay_on_release or (not event.shift)
            if should_stay:
                # 移動先にとどまる（original_frameには戻らない）
                # オフセット状態を方向別に更新
                if self.next:
                    MONKEY_OT_KEYFRAME_PEEK._offset_frames_next = self.current_offset
                else:
                    MONKEY_OT_KEYFRAME_PEEK._offset_frames_prev = self.current_offset
                self.original_frame = None
                return {"FINISHED"}

            # 通常の場合は元のフレームに戻る
            if self.original_frame is not None:
                context.scene.frame_set(self.original_frame)
                # オフセット状態を方向別に更新
                if self.next:
                    MONKEY_OT_KEYFRAME_PEEK._offset_frames_next = self.current_offset
                else:
                    MONKEY_OT_KEYFRAME_PEEK._offset_frames_prev = self.current_offset
                self.original_frame = None
            return {"FINISHED"}

        # peekキーが押され続けている間のリピート/押下イベントは消費して他オペレーターへ渡さない
        if event.type == self.peek_key_type:
            # RELEASE以外（PRESS/REPEAT等）は消費して滞留
            return {"RUNNING_MODAL"}

        # 追加機能: 1キーで前のキーフレームに移動
        if event.type == "ONE" and event.value == "PRESS":
            self.current_offset = self._clamp_offset_by_direction(
                self.current_offset - 1
            )
            self._apply_offset(context)
            return {"RUNNING_MODAL"}

        # 追加機能: 2キーで次のキーフレームに移動
        if event.type == "TWO" and event.value == "PRESS":
            self.current_offset = self._clamp_offset_by_direction(
                self.current_offset + 1
            )
            self._apply_offset(context)
            return {"RUNNING_MODAL"}

        # 追加機能: Qキーでリセット
        if event.type == "Q" and event.value == "PRESS":
            self.current_offset = 0
            MONKEY_OT_KEYFRAME_PEEK._offset_frames_next = 0
            MONKEY_OT_KEYFRAME_PEEK._offset_frames_prev = 0
            self._apply_offset(context)
            return {"RUNNING_MODAL"}

        return {"PASS_THROUGH"}

    def _apply_offset(self, context):
        """オフセットを適用してキーフレーム位置を計算"""
        if self.original_frame is None:
            return

        # 基本位置（オリジナルフレーム + 初期ジャンプ方向）を計算
        base_frame = self._get_base_keyframe_position(context)

        # オフセットを適用
        if self.current_offset == 0:
            # オフセットが0の場合は基本位置
            target_frame = base_frame
        else:
            # オフセットに応じてキーフレーム移動
            target_frame = self._calculate_offset_frame(
                context, base_frame, self.current_offset
            )

        # 基準フレームを跨がないようにクランプ
        context.scene.frame_set(self._clamp_target_frame_by_origin(target_frame))

    def _get_base_keyframe_position(self, context):
        """基本のキーフレーム位置（初期ジャンプ先）を取得"""
        # オリジナルフレームに戻って、初期ジャンプを実行
        context.scene.frame_set(self.original_frame)

        keyframe_jump_in_timeline(context, self.next)

        return context.scene.frame_current

    def _calculate_offset_frame(self, context, base_frame, offset):
        """オフセット分だけキーフレーム移動した位置を計算"""
        context.scene.frame_set(base_frame)

        # 正の値なら次のキーフレーム方向、負の値なら前のキーフレーム方向
        for _ in range(abs(offset)):
            keyframe_jump_in_timeline(context, (offset > 0))

        return context.scene.frame_current

    def invoke(self, context, event):
        # キータイプを設定
        self.peek_key_type = event.type

        # 元のフレームを記憶
        self.original_frame = context.scene.frame_current

        # 保存されたオフセットを方向に応じて適用
        if self.next:
            self.current_offset = MONKEY_OT_KEYFRAME_PEEK._offset_frames_next
        else:
            self.current_offset = MONKEY_OT_KEYFRAME_PEEK._offset_frames_prev

        # 進行方向を跨がないように、符号を方向に合わせてクランプ
        self.current_offset = self._clamp_offset_by_direction(self.current_offset)

        # タイムラインエリアを探す
        # 次のキーフレームへジャンプ（タイムライン基準）
        keyframe_jump_in_timeline(context, self.next)

        # 保存されたオフセットがある場合は追加で適用
        if self.current_offset != 0:
            self._apply_offset(context)

        # モーダル開始
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def _clamp_offset_by_direction(self, offset: int) -> int:
        """進行方向を跨がないようにオフセット符号をクランプ"""
        if self.next:
            return max(0, offset)
        return min(0, offset)

    def _clamp_target_frame_by_origin(self, target_frame: int) -> int:
        """基準フレームを跨がないようにターゲットフレームをクランプ"""
        if self.next:
            # 前方ピーク中は元フレームより前へ行かない（最低 original+1）
            return max(self.original_frame + 1, target_frame)
        # 後方ピーク中は元フレームより後へ行かない（最大 original-1）
        return min(self.original_frame - 1, target_frame)


KEYFRAME_JUMP_KEYMAPS = [
    ("Frames", "EMPTY"),
    ("Object Mode", "EMPTY"),
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


def register():
    # シーンプロパティ: キーフレームジャンプのフィルタタイプ
    try:
        if not hasattr(bpy.types.Scene, "monkey_keyframe_filter_type"):
            # ビットフラグで複数選択可能（'ANY' は特別扱いし、全許可として運用）
            bpy.types.Scene.monkey_keyframe_filter_type = EnumProperty(  # type: ignore
                items=KEYFRAME_TYPE_FLAGS,
                name="Keyframe Jump Filter",
                description="Filter keyframe types (multi-select)",
                options={"ENUM_FLAG", "SKIP_SAVE"},
            )
    except Exception:
        pass

    # タイムラインメニューにUIを追加
    try:
        bpy.types.TIME_MT_editor_menus.append(draw_timeline_filter_menu)
    except Exception:
        pass


def unregister():
    # タイムラインメニューからUIを削除
    try:
        bpy.types.TIME_MT_editor_menus.remove(draw_timeline_filter_menu)
    except Exception:
        pass

    # シーンプロパティを削除
    try:
        if hasattr(bpy.types.Scene, "monkey_keyframe_filter_type"):
            del bpy.types.Scene.monkey_keyframe_filter_type  # type: ignore
    except Exception:
        pass

    # キャッシュのクリア
    try:
        invalidate_allowed_frames_cache()
    except Exception:
        pass
