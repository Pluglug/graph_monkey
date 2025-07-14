import bpy
from ..utils.logging import get_logger
from .dopesheet_helper import get_visible_objects, get_selected_keyframes

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

        if not context.space_data:
            return False

        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        return bool(visible_objects)

    def execute(self, context):
        if not context.space_data:
            self.report({"ERROR"}, "Graph Editor space data not found.")
            return {"CANCELLED"}

        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        toggle_handle_selection(self.handle_direction, self.extend, visible_objects)
        return {"FINISHED"}


def toggle_handle_selection(
    handle_direction: str, extend: bool, visible_objects: list
) -> None:
    if visible_objects is None:
        return

    all_selected = True

    for obj in visible_objects:
        selected_channels = [
            fcurve for fcurve in obj.animation_data.action.fcurves if fcurve.select
        ]

        if selected_channels:
            all_selected &= all_keyframes_have_selected_handle(obj, handle_direction)
            if not all_selected:
                break

    for obj in visible_objects:
        selected_channels = [
            fcurve for fcurve in obj.animation_data.action.fcurves if fcurve.select
        ]

        if selected_channels:
            toggle_keyframe_handle_selection(
                obj, handle_direction, extend, all_selected
            )


def all_keyframes_have_selected_handle(
    obj: bpy.types.Object, handle_direction: str
) -> bool:
    """選択されたキーフレームがすべて指定されたハンドルを選択しているかどうかを返す"""
    action = obj.animation_data.action

    for fcurve in action.fcurves:
        if not fcurve.select:
            continue

        selected = get_selected_keyframes(fcurve.keyframe_points)

        if not selected:
            continue

        for item in selected:
            keyframe = item["keyframe"]

            if handle_direction == "Left":
                if not keyframe.select_left_handle:
                    return False
            elif handle_direction == "Right":
                if not keyframe.select_right_handle:
                    return False
    return True


def toggle_keyframe_handle_selection(
    obj: bpy.types.Object, handle_direction: str, extend: bool, all_selected: bool
) -> None:
    action = obj.animation_data.action

    for fcurve in action.fcurves:
        if not fcurve.select:
            continue

        selected = get_selected_keyframes(fcurve.keyframe_points)

        if not selected:
            continue

        for item in selected:
            keyframe = item["keyframe"]
            update_keyframe_handle_selection(
                keyframe, handle_direction, extend, all_selected
            )


def update_keyframe_handle_selection(keyframe, handle_direction, extend, all_selected):
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
