import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Menu, Operator

from ...keymap_manager import KeymapDefinition, keymap_registry
from ...operators.dopesheet_helper import get_visible_fcurves
from ...utils.logging import get_logger
from ...utils.ui_utils import ic

log = get_logger(__name__)


class MONKEY_OT_graph_key_align_horizontal(Operator):
    """Align selected keyframes horizontally (frame-wise)"""

    bl_idname = "monkey.graph_key_align_horizontal"
    bl_label = "Align Keyframes Horizontally"
    bl_options = {"UNDO"}

    align_type: EnumProperty(
        name="Align Type",
        description="Horizontal align type",
        items=[
            ("LEFT", "Left", "Align keys to the leftmost frame"),
            ("RIGHT", "Right", "Align keys to the rightmost frame"),
        ],
        default="LEFT",
    )

    @classmethod
    def poll(cls, context):
        return (
            context.area
            and context.area.type == "GRAPH_EDITOR"
            and get_visible_fcurves(context)
        )

    def execute(self, context):
        visible_fcurves = get_visible_fcurves(context)
        if not visible_fcurves:
            self.report({"ERROR"}, "No visible F-curves found")
            return {"CANCELLED"}

        # 選択されたキーフレームを収集
        selected_keyframes = []
        affected_fcurves = set()

        for fcurve in visible_fcurves:
            for keyframe in fcurve.keyframe_points:
                if (
                    keyframe.select_control_point
                    or keyframe.select_left_handle
                    or keyframe.select_right_handle
                ):
                    selected_keyframes.append(keyframe)
                    affected_fcurves.add(fcurve)

        if not selected_keyframes:
            self.report({"ERROR"}, "No selected keyframes or handles found")
            return {"CANCELLED"}

        # 選択されている要素の位置を収集
        selected_positions = []
        for keyframe in selected_keyframes:
            if keyframe.select_control_point:
                selected_positions.append(keyframe.co[0])
            if keyframe.select_left_handle:
                selected_positions.append(keyframe.handle_left[0])
            if keyframe.select_right_handle:
                selected_positions.append(keyframe.handle_right[0])

        target_frame = (
            min(selected_positions)
            if self.align_type == "LEFT"
            else max(selected_positions)
        )

        # 同じフレームに移動しようとする場合はスキップ
        if all(abs(pos - target_frame) < 0.001 for pos in selected_positions):
            self.report({"INFO"}, "Selected elements are already aligned")
            return {"FINISHED"}

        # 選択された要素のみを移動
        for keyframe in selected_keyframes:
            if keyframe.select_control_point:
                keyframe.co[0] = target_frame
            if keyframe.select_left_handle:
                keyframe.handle_left[0] = target_frame
            if keyframe.select_right_handle:
                keyframe.handle_right[0] = target_frame

        # 影響のあるF-Curveのみ更新
        for fcurve in affected_fcurves:
            fcurve.update()

        # カウント情報を計算
        control_count = sum(1 for kf in selected_keyframes if kf.select_control_point)
        handle_count = sum(
            1
            for kf in selected_keyframes
            if kf.select_left_handle or kf.select_right_handle
        )

        direction = "left" if self.align_type == "LEFT" else "right"

        if control_count > 0 and handle_count > 0:
            message = f"Aligned {control_count} keyframes and {handle_count} handles to {direction} (frame {target_frame:.2f})"
        elif control_count > 0:
            message = f"Aligned {control_count} keyframes to {direction} (frame {target_frame:.2f})"
        else:
            message = f"Aligned {handle_count} handles to {direction} (frame {target_frame:.2f})"

        self.report({"INFO"}, message)
        return {"FINISHED"}


class MONKEY_OT_graph_key_align_vertical(Operator):
    """Align selected keyframes vertically (value-wise)"""

    bl_idname = "monkey.graph_key_align_vertical"
    bl_label = "Align Keyframes Vertically"
    bl_options = {"UNDO"}

    align_type: EnumProperty(
        name="Align Type",
        description="Vertical align type",
        items=[
            ("TOP", "Top", "Align keys to the highest value"),
            ("BOTTOM", "Bottom", "Align keys to the lowest value"),
        ],
        default="BOTTOM",
    )

    @classmethod
    def poll(cls, context):
        return (
            context.area
            and context.area.type == "GRAPH_EDITOR"
            and get_visible_fcurves(context)
        )

    def execute(self, context):
        visible_fcurves = get_visible_fcurves(context)
        if not visible_fcurves:
            self.report({"ERROR"}, "No visible F-curves found")
            return {"CANCELLED"}

        # 選択されたキーフレームを収集
        selected_keyframes = []
        affected_fcurves = set()

        for fcurve in visible_fcurves:
            for keyframe in fcurve.keyframe_points:
                if (
                    keyframe.select_control_point
                    or keyframe.select_left_handle
                    or keyframe.select_right_handle
                ):
                    selected_keyframes.append(keyframe)
                    affected_fcurves.add(fcurve)

        if not selected_keyframes:
            self.report({"ERROR"}, "No selected keyframes or handles found")
            return {"CANCELLED"}

        # 選択されている要素の値を収集
        selected_values = []
        for keyframe in selected_keyframes:
            if keyframe.select_control_point:
                selected_values.append(keyframe.co[1])
            if keyframe.select_left_handle:
                selected_values.append(keyframe.handle_left[1])
            if keyframe.select_right_handle:
                selected_values.append(keyframe.handle_right[1])

        target_value = (
            max(selected_values) if self.align_type == "TOP" else min(selected_values)
        )

        # 同じ値に移動しようとする場合はスキップ
        if all(abs(val - target_value) < 0.001 for val in selected_values):
            self.report({"INFO"}, "Selected elements are already aligned")
            return {"FINISHED"}

        # 選択された要素のみを移動
        for keyframe in selected_keyframes:
            if keyframe.select_control_point:
                keyframe.co[1] = target_value
            if keyframe.select_left_handle:
                keyframe.handle_left[1] = target_value
            if keyframe.select_right_handle:
                keyframe.handle_right[1] = target_value

        # 影響のあるF-Curveのみ更新
        for fcurve in affected_fcurves:
            fcurve.update()

        # カウント情報を計算
        control_count = sum(1 for kf in selected_keyframes if kf.select_control_point)
        handle_count = sum(
            1
            for kf in selected_keyframes
            if kf.select_left_handle or kf.select_right_handle
        )

        direction = "top" if self.align_type == "TOP" else "bottom"

        if control_count > 0 and handle_count > 0:
            message = f"Aligned {control_count} keyframes and {handle_count} handles to {direction} (value {target_value:.3f})"
        elif control_count > 0:
            message = f"Aligned {control_count} keyframes to {direction} (value {target_value:.3f})"
        else:
            message = f"Aligned {handle_count} handles to {direction} (value {target_value:.3f})"

        self.report({"INFO"}, message)
        return {"FINISHED"}


class MONKEY_MT_GraphKeyAlignPie(Menu):
    bl_idname = "MONKEY_MT_graph_key_align_pie"
    bl_label = "Graph Key Align"

    @classmethod
    def poll(cls, context):
        return context.selected_visible_fcurves

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 選択中のKey, ハンドルを一番低いフレーム数の物に揃える。ハンドルや異なるチャンネルのKeyを選択している場合に効果的。
        # 懸念点: 同じF-CurveのKeyを複数選択している場合は意図しない結果になる。
        l = pie.operator("monkey.graph_key_align_horizontal", icon=ic("TRIA_LEFT"))
        l.align_type = "LEFT"

        # 選択中のKey, ハンドルを一番高いフレーム数の物に揃える
        r = pie.operator("monkey.graph_key_align_horizontal", icon=ic("TRIA_RIGHT"))
        r.align_type = "RIGHT"

        # 選択中のKey, ハンドルを一番値の低いものに揃える
        # 懸念点: こちらは特にない。
        b = pie.operator("monkey.graph_key_align_vertical", icon=ic("TRIA_DOWN"))
        b.align_type = "BOTTOM"

        # 選択中のKey, ハンドルを一番値の高いものに揃える
        t = pie.operator("monkey.graph_key_align_vertical", icon=ic("TRIA_UP"))
        t.align_type = "TOP"


keymap_registry.register_keymap_group(
    group_name="Graph Pie",
    keymaps=[
        KeymapDefinition(
            operator_id="wm.call_menu_pie",
            key="A",
            value="PRESS",
            shift=1,
            alt=1,
            properties={"name": "MONKEY_MT_graph_key_align_pie"},
            name="Graph Editor",
            space_type="GRAPH_EDITOR",
            region_type="WINDOW",
        ),
    ],
)
