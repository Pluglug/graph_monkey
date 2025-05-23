import bpy
from bpy.types import Operator
from bpy.props import BoolProperty


class GRAPH_OT_view_selected_curves_range(Operator):
    """再生範囲内の選択中のカーブ全体を表示する"""

    bl_idname = "graph.view_selected_curves_range"
    bl_label = "View Selected Curves Range"
    bl_options = {"REGISTER", "UNDO"}

    include_handles: BoolProperty(
        name="Include Handles",
        default=True,
    )
    use_frame_range: BoolProperty(
        name="Use Frame Range",
        description="再生範囲またはプレビュー範囲内でフォーカスする",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == "GRAPH_EDITOR"
            and context.selected_editable_fcurves
        )

    def execute(self, context):
        scene = context.scene
        selected_curves = context.selected_editable_fcurves

        if not selected_curves:
            self.report({"WARNING"}, "選択中のFカーブがありません")
            return {"CANCELLED"}

        # 再生範囲の取得
        if self.use_frame_range:
            if scene.use_preview_range:
                frame_start = scene.frame_preview_start
                frame_end = scene.frame_preview_end
            else:
                frame_start = scene.frame_start
                frame_end = scene.frame_end
        else:
            frame_start = float("-inf")
            frame_end = float("inf")

        # 現在の選択状態を保存
        original_selection = {}
        for curve in selected_curves:
            keyframe_states = []
            for kf in curve.keyframe_points:
                keyframe_states.append(
                    {
                        "control": kf.select_control_point,
                        "left": kf.select_left_handle,
                        "right": kf.select_right_handle,
                    }
                )
            original_selection[curve] = keyframe_states

        # キーフレームの選択状態を変更（再生範囲内のすべてのキーフレームを選択）
        for curve in selected_curves:
            for keyframe in curve.keyframe_points:
                x = keyframe.co[0]
                in_range = frame_start <= x <= frame_end
                keyframe.select_control_point = in_range
                keyframe.select_left_handle = in_range
                keyframe.select_right_handle = in_range

        # graph.view_selectedを実行してフォーカス
        bpy.ops.graph.view_selected(include_handles=self.include_handles)

        # 元の選択状態に戻す
        for curve in selected_curves:
            if curve in original_selection:
                for i, state in enumerate(original_selection[curve]):
                    if i < len(curve.keyframe_points):
                        kf = curve.keyframe_points[i]
                        kf.select_control_point = state["control"]
                        kf.select_left_handle = state["left"]
                        kf.select_right_handle = state["right"]

        return {"FINISHED"}


# def menu_func(self, context):
#     self.layout.operator(GRAPH_OT_view_selected_curves_range.bl_idname)


# def register():
#     bpy.utils.register_class(GRAPH_OT_view_selected_curves_range)
#     bpy.types.GRAPH_MT_view.append(menu_func)


# def unregister():
#     bpy.types.GRAPH_MT_view.remove(menu_func)
#     bpy.utils.unregister_class(GRAPH_OT_view_selected_curves_range)


# if __name__ == "__main__":
#     register()
