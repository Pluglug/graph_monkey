import bpy
from ..utils.logging import get_logger

log = get_logger(__name__)


def is_object_displayed(obj, dopesheet, type_filters):
    # Check if the object's type is shown
    obj_type = obj.type
    if obj_type in type_filters and not type_filters[obj_type]:
        return False

    # Check if the object is selected
    if dopesheet.show_only_selected and not obj.select_get():
        return False

    # Check if the object is hidden
    if not dopesheet.show_hidden and obj.hide_viewport:
        return False

    return True


# def check_graph_editor_and_visible_objects():
#     graph_editor = None
#     for area in bpy.context.screen.areas:
#         if area.type == 'GRAPH_EDITOR':
#             graph_editor = area.spaces.active
#             break
#
#     if graph_editor is None:
#         print("Graph Editor not found.")
#         return None, None
#
#     dopesheet = graph_editor.dopesheet
#
#     visible_objects = get_visible_objects(dopesheet)
#
#     if not visible_objects:
#         print("There is no object that is displayed and has an action.")
#         return None, None
#
#     return graph_editor, visible_objects


def get_visible_objects(dopesheet):
    if not bpy.context.scene:
        return []

    type_filters = {
        "SCENE": dopesheet.show_scenes,
        "NODETREE": dopesheet.show_nodes,
        "CAMERA": dopesheet.show_cameras,
        "LIGHT": dopesheet.show_lights,
        "MESH": dopesheet.show_meshes,
        "WORLD": dopesheet.show_worlds,
        "LINESTYLE": dopesheet.show_linestyles,
        "MATERIAL": dopesheet.show_materials,
    }
    visible_objects = [
        obj
        for obj in bpy.context.scene.objects
        if obj.animation_data
        and obj.animation_data.action
        and is_object_displayed(obj, dopesheet, type_filters)
    ]
    visible_objects.sort(key=lambda obj: obj.name)
    return visible_objects


# keyframe_helpers.py
def get_selected_keyframes(keyframe_points):
    """選択されたキーフレームのリストとその選択状態を返す"""
    return [
        {
            "keyframe": keyframe,
            "control_point": keyframe.select_control_point,
            "left_handle": keyframe.select_left_handle,
            "right_handle": keyframe.select_right_handle,
        }
        for keyframe in keyframe_points
        if keyframe.select_control_point
        or keyframe.select_left_handle
        or keyframe.select_right_handle
    ]


def get_visible_fcurves(context):
    """bpy.context.visible_fcurvesを安全に取得する"""
    if not context or not hasattr(context, "visible_fcurves"):
        return []
    return context.visible_fcurves


def get_selected_visible_fcurves(context):
    """可視状態で選択されたFカーブを取得する"""
    visible_fcurves = get_visible_fcurves(context)
    return [fcurve for fcurve in visible_fcurves if fcurve.select]


def get_all_visible_fcurves(context):
    """すべての可視Fカーブを取得する（選択状態に関係なく）"""
    return get_visible_fcurves(context)
