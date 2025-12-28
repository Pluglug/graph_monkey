# pyright: reportInvalidTypeForm=false
import bpy

from ..keymap_manager import KeymapDefinition, keymap_registry
from ..utils.logging import get_logger
from .dopesheet_helper import (
    get_selected_keyframes,
    get_visible_fcurves,
)

log = get_logger(__name__)

# Keyframe handle selection toggling operator


class GRAPH_OT_monkey_handle_selecter(bpy.types.Operator):
    bl_idname = "graph.monkey_handle_selecter"
    bl_label = "Toggle Handle Selection"
    bl_options = {"UNDO"}

    handle_direction: bpy.props.EnumProperty(  # type: ignore
        name="Handle Direction",
        items=[("Left", "Left", ""), ("Right", "Right", "")],
        default="Left",
    )
    extend: bpy.props.BoolProperty(default=False)  # type: ignore

    @classmethod
    def poll(cls, context):
        if not context.area or context.area.type != "GRAPH_EDITOR":
            return False

        # 新しいアプローチ: visible_fcurvesを使用
        visible_fcurves = get_visible_fcurves(context)
        return bool(visible_fcurves)

    def execute(self, context):
        # 新しいアプローチ: bpy.context.visible_fcurvesを使用
        visible_fcurves = get_visible_fcurves(context)
        if not visible_fcurves:
            self.report({"ERROR"}, "No visible fcurves found")
            return {"CANCELLED"}

        toggle_handle_selection(self.handle_direction, self.extend)
        return {"FINISHED"}


def toggle_handle_selection(handle_direction: str, extend: bool) -> None:
    """ハンドル選択を切り替える（新しいアプローチ）"""
    if handle_direction not in ("Left", "Right"):
        raise ValueError("Invalid handle direction. Must be 'Left' or 'Right'.")

    # 新しいヘルパー関数を使用して可視Fカーブを取得
    visible_fcurves = get_visible_fcurves(bpy.context)

    if not visible_fcurves:
        log.warning("No visible fcurves found")
        return

    # 選択されたFカーブのみを処理
    selected_fcurves = [fcurve for fcurve in visible_fcurves if fcurve.select]

    if not selected_fcurves:
        log.warning("No selected fcurves found")
        return

    # すべての選択されたキーフレームが指定されたハンドルを選択しているかチェック
    all_selected = all(
        all_keyframes_have_selected_handle_for_fcurve(fcurve, handle_direction)
        for fcurve in selected_fcurves
    )

    # 各Fカーブのハンドル選択を切り替え
    for fcurve in selected_fcurves:
        toggle_keyframe_handle_selection_for_fcurve(
            fcurve, handle_direction, extend, all_selected
        )


def all_keyframes_have_selected_handle_for_fcurve(
    fcurve, handle_direction: str
) -> bool:
    """Fカーブの選択されたキーフレームがすべて指定されたハンドルを選択しているかどうかを返す"""
    selected = get_selected_keyframes(fcurve.keyframe_points)

    if not selected:
        return True  # 選択されたキーフレームがない場合はTrueを返す

    for item in selected:
        keyframe = item["keyframe"]

        if handle_direction == "Left":
            if not keyframe.select_left_handle:
                return False
        elif handle_direction == "Right":
            if not keyframe.select_right_handle:
                return False
    return True


def toggle_keyframe_handle_selection_for_fcurve(
    fcurve, handle_direction: str, extend: bool, all_selected: bool
) -> None:
    """Fカーブのキーフレームハンドル選択を切り替える"""
    selected = get_selected_keyframes(fcurve.keyframe_points)

    if not selected:
        return

    for item in selected:
        keyframe = item["keyframe"]
        update_keyframe_handle_selection(
            keyframe, handle_direction, extend, all_selected
        )


def update_keyframe_handle_selection(keyframe, handle_direction, extend, all_selected):
    """キーフレームのハンドル選択状態を更新する"""
    if handle_direction == "Left":
        if all_selected:
            keyframe.select_left_handle = False
            keyframe.select_control_point = True
        else:
            if not extend:
                keyframe.select_right_handle = False
                keyframe.select_control_point = False
            keyframe.select_left_handle = True
    elif handle_direction == "Right":
        if all_selected:
            keyframe.select_right_handle = False
            keyframe.select_control_point = True
        else:
            if not extend:
                keyframe.select_left_handle = False
                keyframe.select_control_point = False
            keyframe.select_right_handle = True


keymap_monkey_handle_selecter = [
    # ハンドル選択 Left
    KeymapDefinition(
        operator_id="graph.monkey_handle_selecter",
        key="Q",
        value="PRESS",
        alt=True,
        shift=False,
        properties={"handle_direction": "Left", "extend": False},
        name="Graph Editor",
        space_type="GRAPH_EDITOR",
        description="左ハンドル選択",
    ),
    # ハンドル選択 Left（拡張）
    KeymapDefinition(
        operator_id="graph.monkey_handle_selecter",
        key="Q",
        value="PRESS",
        alt=True,
        shift=True,
        properties={"handle_direction": "Left", "extend": True},
        name="Graph Editor",
        space_type="GRAPH_EDITOR",
        description="左ハンドル選択（拡張）",
    ),
    # ハンドル選択 Right
    KeymapDefinition(
        operator_id="graph.monkey_handle_selecter",
        key="E",
        value="PRESS",
        alt=True,
        shift=False,
        properties={"handle_direction": "Right", "extend": False},
        name="Graph Editor",
        space_type="GRAPH_EDITOR",
        description="右ハンドル選択",
    ),
    # ハンドル選択 Right（拡張）
    KeymapDefinition(
        operator_id="graph.monkey_handle_selecter",
        key="E",
        value="PRESS",
        alt=True,
        shift=True,
        properties={"handle_direction": "Right", "extend": True},
        name="Graph Editor",
        space_type="GRAPH_EDITOR",
        description="右ハンドル選択（拡張）",
    ),
]

keymap_registry.register_keymap_group(
    "Monkey Handle Selection", keymap_monkey_handle_selecter
)
